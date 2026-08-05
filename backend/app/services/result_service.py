import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai import AIProvider
from app.core.errors import NotFoundError, TransitionError
from app.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentResult,
    CostItem,
    EvidenceObservation,
    EvidenceRequest,
    ProcessStep,
    Recommendation,
    Requirement,
    RequirementEvaluation,
    RoadmapItem,
)
from app.models.enums import AssessmentStatus, EvidenceRequestStatus
from app.schemas.ai import (
    RoadmapExplanationInput,
    RoadmapExplanationsOutput,
)
from app.services.ai_service import run_with_validation
from app.services.assessment_service import update_assessment_progress
from app.services.clarification_service import ensure_assessment_complete
from app.services.requirement_engine import EvaluatedRequirement, evaluate_all_requirements
from app.services.roadmap_engine import (
    RoadmapDraft,
    calculate_cost_summary,
)
from app.services.roadmap_engine import (
    build_roadmap as build_deterministic_roadmap,
)
from app.services.scoring_engine import (
    calculate_category_scores,
    calculate_evidence_completeness,
    calculate_readiness_score,
    display_round,
)

DISCLAIMER = (
    "CertifyLK is a readiness-assessment tool and does not issue, guarantee, or replace "
    "SLS certification or an official inspection."
)
SCORING_VERSION = "phase1-v1"


def _answer_map(db: Session, assessment_id: uuid.UUID) -> dict[str, str]:
    answers = list(
        db.scalars(select(AssessmentAnswer).where(AssessmentAnswer.assessment_id == assessment_id))
    )
    result: dict[str, str] = {}
    for answer in answers:
        if answer.page == "profile":
            continue
        result[answer.key] = (
            str(answer.value.get("value")) if isinstance(answer.value, dict) else str(answer.value)
        )
    return result


def _evaluation_summary(item: EvaluatedRequirement) -> dict[str, object]:
    return {
        "requirement_id": item.requirement_id,
        "title": item.title,
        "status": item.status.value,
        "rationale": item.rationale,
        "evidence_references": item.evidence_references,
    }


def _build_unavailable_map(requests: list[EvidenceRequest]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for request in requests:
        if request.status != EvidenceRequestStatus.UNAVAILABLE:
            continue
        for requirement_id in request.requirement_ids:
            output.setdefault(requirement_id, []).append(request.evidence_type)
    return output


async def generate_result(db: Session, assessment: Assessment) -> AssessmentResult:
    existing = db.scalar(
        select(AssessmentResult).where(AssessmentResult.assessment_id == assessment.id)
    )
    if existing is not None and assessment.status == AssessmentStatus.COMPLETED:
        return existing
    ensure_assessment_complete(db, assessment)

    requirements = list(
        db.scalars(select(Requirement).where(Requirement.active.is_(True)).order_by(Requirement.id))
    )
    if not requirements:
        raise TransitionError("The readiness catalogue has not been seeded.")
    steps = list(db.scalars(select(ProcessStep).where(ProcessStep.assessment_id == assessment.id)))
    observations = list(
        db.scalars(
            select(EvidenceObservation).where(EvidenceObservation.assessment_id == assessment.id)
        )
    )
    observation_data = [
        {
            "id": str(item.id),
            "requirement_id": item.requirement_id,
            "polarity": item.polarity.value,
            "confidence": Decimal(item.confidence),
        }
        for item in observations
    ]
    evidence_requests = list(
        db.scalars(select(EvidenceRequest).where(EvidenceRequest.assessment_id == assessment.id))
    )
    evaluations = evaluate_all_requirements(
        requirements,
        answers=_answer_map(db, assessment.id),
        profile=assessment.profile_data,
        non_empty_process_steps=sum(bool(step.text.strip()) for step in steps),
        observations=observation_data,
        unavailable_by_requirement=_build_unavailable_map(evidence_requests),
    )
    category_scores = calculate_category_scores(evaluations)
    raw_score = calculate_readiness_score(category_scores)
    completeness = calculate_evidence_completeness(evaluations)
    recommendations = list(
        db.scalars(
            select(Recommendation)
            .where(Recommendation.active.is_(True))
            .order_by(Recommendation.id)
        )
    )
    costs = list(db.scalars(select(CostItem).order_by(CostItem.recommendation_id)))
    drafts = build_deterministic_roadmap(evaluations, recommendations, costs, raw_score)
    explanation_inputs = [
        RoadmapExplanationInput(
            recommendation_id=draft.recommendation.id,
            title=draft.recommendation.title,
            implementation_steps=draft.recommendation.implementation_steps,
            affected_titles=[item.title for item in draft.affected],
        )
        for draft in drafts
    ]
    explanations: dict[str, str] = {}
    if explanation_inputs:
        expected_ids = {item.recommendation_id for item in explanation_inputs}

        async def call(provider: AIProvider) -> RoadmapExplanationsOutput:
            return await provider.explain_roadmap(explanation_inputs)

        def validate(output: RoadmapExplanationsOutput) -> None:
            returned = [item.recommendation_id for item in output.explanations]
            if set(returned) != expected_ids or len(returned) != len(expected_ids):
                raise ValueError("Roadmap explanations must match supplied recommendation IDs")

        output = await run_with_validation(db, assessment.id, "explain_roadmap", call, validate)
        explanations = {item.recommendation_id: item.explanation for item in output.explanations}

    db.execute(
        delete(RequirementEvaluation).where(RequirementEvaluation.assessment_id == assessment.id)
    )
    now = datetime.now(timezone.utc)
    for item in evaluations:
        db.add(
            RequirementEvaluation(
                assessment_id=assessment.id,
                requirement_id=item.requirement_id,
                status=item.status,
                multiplier=item.multiplier,
                evidence_references=item.evidence_references,
                rationale=item.rationale,
            )
        )

    strengths = [
        _evaluation_summary(item) for item in evaluations if item.status.value == "confirmed"
    ]
    gaps = [
        _evaluation_summary(item) for item in evaluations if item.status.value in {"gap", "partial"}
    ]
    unknowns = [_evaluation_summary(item) for item in evaluations if item.status.value == "unknown"]
    serializable_categories = [
        {**score, "score_raw": str(score["score_raw"])} for score in category_scores
    ]
    cost_summary = calculate_cost_summary(drafts)
    result = AssessmentResult(
        assessment_id=assessment.id,
        overall_score_raw=raw_score,
        overall_score=display_round(raw_score),
        evidence_completeness=completeness,
        category_scores=serializable_categories,
        strengths=strengths,
        gaps=gaps,
        unknowns=unknowns,
        cost_summary=cost_summary,
        scoring_version=SCORING_VERSION,
    )
    db.add(result)
    db.flush()
    for order, draft in enumerate(drafts, start=1):
        db.add(
            RoadmapItem(
                result_id=result.id,
                assessment_id=assessment.id,
                recommendation_id=draft.recommendation.id,
                display_order=order,
                priority_tier=draft.tier,
                expected_gain=draft.gain,
                projected_score_raw=draft.projected_score,
                cost_snapshot=_cost_snapshot(draft),
                explanation=explanations.get(
                    draft.recommendation.id,
                    f"This action addresses {draft.affected[0].title.lower()}.",
                ),
                created_at=now,
            )
        )
    update_assessment_progress(assessment, AssessmentStatus.COMPLETED)
    db.commit()
    return result


def _cost_snapshot(draft: RoadmapDraft) -> dict[str, object]:
    return {
        "one_time": {
            "min": draft.cost.one_time_min,
            "max": draft.cost.one_time_max,
            "currency": draft.cost.currency,
        },
        "recurring": {
            "min": draft.cost.recurring_min,
            "max": draft.cost.recurring_max,
            "currency": draft.cost.currency,
        },
        "cost_note": draft.recommendation.cost_note,
        "last_reviewed": draft.cost.last_reviewed.isoformat(),
    }


def get_result(db: Session, assessment: Assessment) -> AssessmentResult:
    if assessment.status != AssessmentStatus.COMPLETED:
        raise TransitionError("Complete the assessment before retrieving its result.")
    result = db.scalar(
        select(AssessmentResult).where(AssessmentResult.assessment_id == assessment.id)
    )
    if result is None:
        raise NotFoundError("Assessment result not found.")
    return result


def serialize_result(
    db: Session, assessment: Assessment, result: AssessmentResult
) -> dict[str, object]:
    roadmap_items = list(
        db.scalars(
            select(RoadmapItem)
            .where(RoadmapItem.result_id == result.id)
            .order_by(RoadmapItem.display_order)
        )
    )
    return {
        "assessment_id": assessment.id,
        "overall_score_raw": result.overall_score_raw,
        "overall_score": result.overall_score,
        "evidence_completeness": result.evidence_completeness,
        "category_scores": result.category_scores,
        "strengths": result.strengths,
        "gaps": result.gaps,
        "unknowns": result.unknowns,
        "roadmap": [
            {
                "recommendation_id": item.recommendation_id,
                "title": item.recommendation.title,
                "implementation_steps": item.recommendation.implementation_steps,
                "priority": item.priority_tier,
                "one_time_cost": item.cost_snapshot["one_time"],
                "recurring_cost": item.cost_snapshot["recurring"],
                "cost_note": item.cost_snapshot["cost_note"],
                "last_reviewed": item.cost_snapshot["last_reviewed"],
                "expected_gain": float(item.expected_gain),
                "projected_score": display_round(Decimal(item.projected_score_raw)),
                "explanation": item.explanation,
            }
            for item in roadmap_items
        ],
        "cost_summary": result.cost_summary,
        "disclaimer": DISCLAIMER,
    }
