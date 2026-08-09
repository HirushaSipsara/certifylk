import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import cast

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai import AIProvider
from app.core.errors import NotFoundError, TransitionError
from app.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentResult,
    CertificationScheme,
    CostItem,
    EvidenceObservation,
    EvidenceRequest,
    ProcessStep,
    Recommendation,
    Requirement,
    RequirementEvaluation,
    RoadmapItem,
    SchemeCostItem,
)
from app.models.enums import AssessmentStatus, EvidenceRequestStatus, RequirementStatus
from app.schemas.ai import (
    RoadmapExplanationInput,
    RoadmapExplanationsOutput,
)
from app.services.ai_service import run_with_validation
from app.services.assessment_service import update_assessment_progress
from app.services.catalog_service import get_scheme_cost_items, get_scheme_requirements
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
SCHEME_SCORING_VERSION = "scheme-v1"


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

        execution = await run_with_validation(db, assessment.id, "explain_roadmap", call, validate)
        output = execution.output
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
        # Preserve certificate context even when this legacy-compatible scoring
        # path is used for a scheme-backed sample assessment.
        scheme_id=assessment.scheme_id,
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


async def generate_scheme_result(db: Session, assessment: Assessment) -> AssessmentResult:
    if not assessment.scheme_id:
        raise TransitionError("Select a certification scheme before scoring this assessment.")
    existing = db.scalar(
        select(AssessmentResult).where(AssessmentResult.assessment_id == assessment.id)
    )
    if existing is not None and assessment.status == AssessmentStatus.COMPLETED:
        return existing
    ensure_assessment_complete(db, assessment)

    scheme = db.get(CertificationScheme, assessment.scheme_id)
    if scheme is None:
        raise TransitionError("The selected certification scheme is no longer available.")
    requirements = get_scheme_requirements(db, scheme.id)
    if not requirements:
        raise TransitionError("The selected certification scheme has no active requirements.")
    if assessment.scheme_version is None:
        assessment.scheme_version = scheme.standard_version
    if assessment.catalogue_revision is None:
        assessment.catalogue_revision = scheme.catalogue_revision

    steps = list(db.scalars(select(ProcessStep).where(ProcessStep.assessment_id == assessment.id)))
    observations = list(
        db.scalars(
            select(EvidenceObservation).where(EvidenceObservation.assessment_id == assessment.id)
        )
    )
    allowed_requirement_ids = {item.id for item in requirements}
    observation_data = [
        {
            "id": str(item.id),
            "requirement_id": item.requirement_id,
            "polarity": item.polarity.value,
            "confidence": Decimal(item.confidence),
        }
        for item in observations
        if item.requirement_id in allowed_requirement_ids
    ]
    evidence_requests = [
        request
        for request in db.scalars(
            select(EvidenceRequest).where(EvidenceRequest.assessment_id == assessment.id)
        )
        if set(request.requirement_ids).issubset(allowed_requirement_ids)
    ]
    evaluations = evaluate_all_requirements(
        requirements,
        answers=_answer_map(db, assessment.id),
        profile=assessment.profile_data,
        non_empty_process_steps=sum(bool(step.text.strip()) for step in steps),
        observations=observation_data,
        unavailable_by_requirement=_build_unavailable_map(evidence_requests),
    )
    category_scores = calculate_category_scores(evaluations, _category_weights(scheme))
    raw_score = calculate_readiness_score(category_scores)
    completeness = calculate_evidence_completeness(evaluations)
    costs = get_scheme_cost_items(db, scheme.id)
    roadmap_snapshot = await _scheme_roadmap_snapshot(db, assessment, evaluations, costs, raw_score)

    db.execute(
        delete(RequirementEvaluation).where(RequirementEvaluation.assessment_id == assessment.id)
    )
    for item in evaluations:
        db.add(
            RequirementEvaluation(
                assessment_id=assessment.id,
                requirement_id=item.requirement_id,
                scheme_id=scheme.id,
                scheme_requirement_id=item.requirement_id,
                status=item.status,
                multiplier=item.multiplier,
                evidence_references=item.evidence_references,
                rationale=item.rationale,
            )
        )

    serializable_categories = [
        {**score, "score_raw": str(score["score_raw"])} for score in category_scores
    ]
    result = AssessmentResult(
        assessment_id=assessment.id,
        overall_score_raw=raw_score,
        overall_score=display_round(raw_score),
        evidence_completeness=completeness,
        category_scores=serializable_categories,
        strengths=[
            _evaluation_summary(item) for item in evaluations if item.status.value == "confirmed"
        ],
        gaps=[
            _evaluation_summary(item)
            for item in evaluations
            if item.status.value in {"gap", "partial"}
        ],
        unknowns=[
            _evaluation_summary(item) for item in evaluations if item.status.value == "unknown"
        ],
        cost_summary=_scheme_cost_summary(roadmap_snapshot),
        roadmap_snapshot=roadmap_snapshot,
        scheme_id=scheme.id,
        scheme_version=assessment.scheme_version,
        catalogue_revision=assessment.catalogue_revision,
        scoring_version=SCHEME_SCORING_VERSION,
    )
    db.add(result)
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


def _category_weights(scheme: CertificationScheme) -> dict[str, int]:
    return {str(key): int(value) for key, value in scheme.category_weights.items()}


def _scheme_cost_matches(cost: SchemeCostItem, requirement: EvaluatedRequirement) -> bool:
    haystack = f"{cost.action_ref} {cost.title} {requirement.category} {requirement.title}".lower()
    category = requirement.category.lower()
    if any(term in haystack for term in ("label", "packaging")):
        return "label" in category or "packag" in category or "label" in requirement.title.lower()
    if any(
        term in haystack for term in ("doc", "record", "plan", "procedure", "register", "training")
    ):
        return any(
            term in f"{category} {requirement.title.lower()}"
            for term in ("document", "record", "plan", "procedure", "training", "haccp")
        )
    if any(term in haystack for term in ("lab", "test", "micro", "brix", "water")):
        return any(
            term in requirement.title.lower()
            for term in ("test", "micro", "brix", "water", "limit", "validation")
        )
    if any(term in haystack for term in ("thermometer", "calibrat", "temperature", "equipment")):
        return any(
            term in requirement.title.lower()
            for term in ("temperature", "calibration", "equipment", "critical limit")
        )
    if "pest" in haystack:
        return "pest" in requirement.title.lower() or "pest" in category
    if any(term in haystack for term in ("audit", "application", "certification", "consult")):
        return requirement.status in {
            RequirementStatus.GAP,
            RequirementStatus.PARTIAL,
            RequirementStatus.UNKNOWN,
        }
    return False


def _scheme_priority(cost: SchemeCostItem, affected: list[EvaluatedRequirement]) -> int:
    if any(item.safety_critical and item.status == RequirementStatus.GAP for item in affected):
        return 1
    if max(item.weight for item in affected) >= Decimal("5"):
        return 2
    uncovered_weight = sum(
        (item.weight * (Decimal("1") - item.multiplier) for item in affected), Decimal("0")
    )
    if cost.one_time_max <= 5000 and uncovered_weight >= Decimal("2"):
        return 3
    if any(
        "document" in item.category.lower() or "record" in item.category.lower()
        for item in affected
    ):
        return 4
    if cost.cost_type.value == "business_capex":
        return 5
    return 4


def _scheme_steps(cost: SchemeCostItem, affected: list[EvaluatedRequirement]) -> list[str]:
    titles = ", ".join(item.title for item in affected[:3])
    return [
        f"Review the selected scheme requirement(s): {titles}.",
        "Collect the missing records, controls, photos, declarations, or third-party evidence.",
        "Keep the evidence with the relevant batch, product, or management-system record for review.",
    ]


async def _scheme_roadmap_snapshot(
    db: Session,
    assessment: Assessment,
    evaluations: list[EvaluatedRequirement],
    costs: list[SchemeCostItem],
    current_score: Decimal,
) -> list[dict[str, object]]:
    uncovered = [
        item
        for item in evaluations
        if item.status
        in {RequirementStatus.GAP, RequirementStatus.PARTIAL, RequirementStatus.UNKNOWN}
    ]
    drafts: list[tuple[SchemeCostItem, list[EvaluatedRequirement], int]] = []
    for cost in costs:
        affected = [item for item in uncovered if _scheme_cost_matches(cost, item)]
        if affected:
            drafts.append((cost, affected, _scheme_priority(cost, affected)))
    drafts.sort(
        key=lambda item: (
            item[2],
            -sum(req.weight * (Decimal("1") - req.multiplier) for req in item[1]),
            item[0].one_time_max,
            item[0].id,
        )
    )

    already_covered: set[str] = set()
    projections: list[Decimal] = []
    snapshots: list[dict[str, object]] = []
    projected = current_score
    for order, (cost, affected, tier) in enumerate(drafts, start=1):
        gain = Decimal("0")
        for requirement in affected:
            if requirement.requirement_id in already_covered:
                continue
            gain += requirement.weight * (Decimal("1") - requirement.multiplier)
            already_covered.add(requirement.requirement_id)
        gain = gain.quantize(Decimal("0.001"))
        projected = min(Decimal("100"), projected + gain).quantize(Decimal("0.0001"))
        projections.append(projected)
        quote_required = bool(getattr(cost, "is_quote_required", False))
        snapshots.append(
            {
                "recommendation_id": cost.id,
                "scheme_cost_item_id": cost.id,
                "action_ref": cost.action_ref,
                "title": cost.title,
                "implementation_steps": _scheme_steps(cost, affected),
                "priority": tier,
                "cost_type": cost.cost_type.value
                if hasattr(cost.cost_type, "value")
                else str(cost.cost_type),
                "one_time_cost": {
                    "min": cost.one_time_min,
                    "max": cost.one_time_max,
                    "currency": cost.currency,
                },
                "recurring_cost": {
                    "min": cost.recurring_min,
                    "max": cost.recurring_max,
                    "currency": cost.currency,
                },
                "cost_note": cost.source_note,
                "source_note": cost.source_note,
                "effective_date": cost.effective_date.isoformat(),
                "last_reviewed": cost.last_reviewed.isoformat(),
                "quote_required": quote_required,
                "expected_gain": float(gain),
                "projected_score": display_round(projected),
                "explanation": f"This action addresses {affected[0].title.lower()}.",
                "affected_requirement_ids": [item.requirement_id for item in affected],
                "display_order": order,
            }
        )

    if snapshots:
        explanation_inputs = [
            RoadmapExplanationInput(
                recommendation_id=str(item["recommendation_id"]),
                title=str(item["title"]),
                implementation_steps=cast(list[str], item["implementation_steps"]),
                affected_titles=[
                    requirement.title
                    for requirement in uncovered
                    if requirement.requirement_id
                    in cast(list[str], item["affected_requirement_ids"])
                ],
            )
            for item in snapshots
        ]
        expected_ids = {item.recommendation_id for item in explanation_inputs}

        async def call(provider: AIProvider) -> RoadmapExplanationsOutput:
            return await provider.explain_roadmap(explanation_inputs)

        def validate(output: RoadmapExplanationsOutput) -> None:
            returned = [item.recommendation_id for item in output.explanations]
            if set(returned) != expected_ids or len(returned) != len(expected_ids):
                raise ValueError("Roadmap explanations must match supplied scheme cost IDs")

        try:
            execution = await run_with_validation(
                db, assessment.id, "explain_roadmap", call, validate
            )
            explanations = {
                item.recommendation_id: item.explanation for item in execution.output.explanations
            }
            for item in snapshots:
                item["explanation"] = explanations.get(
                    str(item["recommendation_id"]), item["explanation"]
                )
        except Exception:
            pass
    return snapshots


def _scheme_cost_summary(snapshots: list[dict[str, object]]) -> dict[str, object]:
    by_type: dict[str, dict[str, object]] = {
        "certifying_body_fee": {
            "one_time_min": 0,
            "one_time_max": 0,
            "recurring_min": 0,
            "recurring_max": 0,
            "items_count": 0,
            "quote_required_count": 0,
        },
        "lab_testing_fee": {
            "one_time_min": 0,
            "one_time_max": 0,
            "recurring_min": 0,
            "recurring_max": 0,
            "items_count": 0,
            "quote_required_count": 0,
        },
        "business_capex": {
            "one_time_min": 0,
            "one_time_max": 0,
            "recurring_min": 0,
            "recurring_max": 0,
            "items_count": 0,
            "quote_required_count": 0,
        },
        "business_opex": {
            "one_time_min": 0,
            "one_time_max": 0,
            "recurring_min": 0,
            "recurring_max": 0,
            "items_count": 0,
            "quote_required_count": 0,
        },
    }

    for item in snapshots:
        ctype = str(item.get("cost_type", "business_opex"))
        if ctype not in by_type:
            by_type[ctype] = {
                "one_time_min": 0,
                "one_time_max": 0,
                "recurring_min": 0,
                "recurring_max": 0,
                "items_count": 0,
                "quote_required_count": 0,
            }

        is_quote = bool(item.get("quote_required", False))
        by_type[ctype]["items_count"] = cast(int, by_type[ctype]["items_count"]) + 1

        if is_quote:
            by_type[ctype]["quote_required_count"] = (
                cast(int, by_type[ctype]["quote_required_count"]) + 1
            )
        else:
            ot = cast(dict[str, object], item["one_time_cost"])
            rec = cast(dict[str, object], item["recurring_cost"])
            by_type[ctype]["one_time_min"] = cast(
                int, by_type[ctype]["one_time_min"]
            ) + _snapshot_int(ot["min"])
            by_type[ctype]["one_time_max"] = cast(
                int, by_type[ctype]["one_time_max"]
            ) + _snapshot_int(ot["max"])
            by_type[ctype]["recurring_min"] = cast(
                int, by_type[ctype]["recurring_min"]
            ) + _snapshot_int(rec["min"])
            by_type[ctype]["recurring_max"] = cast(
                int, by_type[ctype]["recurring_max"]
            ) + _snapshot_int(rec["max"])

    overall_one_time_min = sum(cast(int, sub["one_time_min"]) for sub in by_type.values())
    overall_one_time_max = sum(cast(int, sub["one_time_max"]) for sub in by_type.values())
    overall_recurring_min = sum(cast(int, sub["recurring_min"]) for sub in by_type.values())
    overall_recurring_max = sum(cast(int, sub["recurring_max"]) for sub in by_type.values())

    return {
        "one_time_min": overall_one_time_min,
        "one_time_max": overall_one_time_max,
        "recurring_min": overall_recurring_min,
        "recurring_max": overall_recurring_max,
        "currency": "LKR",
        "by_type": by_type,
    }


def _snapshot_int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError("Cost snapshot value must be an integer.")


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
    if result.roadmap_snapshot:
        roadmap = [
            {
                "recommendation_id": item["recommendation_id"],
                "scheme_cost_item_id": item.get("scheme_cost_item_id", item["recommendation_id"]),
                "action_ref": item.get("action_ref", ""),
                "title": item["title"],
                "implementation_steps": item["implementation_steps"],
                "priority": item["priority"],
                "cost_type": item.get("cost_type", "business_opex"),
                "one_time_cost": item["one_time_cost"],
                "recurring_cost": item["recurring_cost"],
                "cost_note": item.get("cost_note", ""),
                "source_note": item.get("source_note", item.get("cost_note", "")),
                "effective_date": item.get("effective_date", ""),
                "last_reviewed": item["last_reviewed"],
                "quote_required": item.get("quote_required", False),
                "expected_gain": item["expected_gain"],
                "projected_score": item["projected_score"],
                "explanation": item["explanation"],
            }
            for item in sorted(result.roadmap_snapshot, key=lambda value: value["display_order"])
        ]
    else:
        roadmap_items = list(
            db.scalars(
                select(RoadmapItem)
                .where(RoadmapItem.result_id == result.id)
                .order_by(RoadmapItem.display_order)
            )
        )
        roadmap = [
            {
                "recommendation_id": item.recommendation_id,
                "scheme_cost_item_id": item.recommendation_id,
                "action_ref": "",
                "title": item.recommendation.title,
                "implementation_steps": item.recommendation.implementation_steps,
                "priority": item.priority_tier,
                "cost_type": "business_capex" if item.recommendation.is_capex else "business_opex",
                "one_time_cost": item.cost_snapshot["one_time"],
                "recurring_cost": item.cost_snapshot["recurring"],
                "cost_note": item.cost_snapshot["cost_note"],
                "source_note": item.cost_snapshot["cost_note"],
                "effective_date": item.cost_snapshot.get("effective_date", ""),
                "last_reviewed": item.cost_snapshot["last_reviewed"],
                "quote_required": False,
                "expected_gain": float(item.expected_gain),
                "projected_score": display_round(Decimal(item.projected_score_raw)),
                "explanation": item.explanation,
            }
            for item in roadmap_items
        ]
    return {
        "assessment_id": assessment.id,
        "overall_score_raw": result.overall_score_raw,
        "overall_score": result.overall_score,
        "evidence_completeness": result.evidence_completeness,
        "category_scores": result.category_scores,
        "strengths": result.strengths,
        "gaps": result.gaps,
        "unknowns": result.unknowns,
        "roadmap": roadmap,
        "cost_summary": result.cost_summary,
        "disclaimer": DISCLAIMER,
        "scheme_id": result.scheme_id or assessment.scheme_id,
    }
