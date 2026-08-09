import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import TransitionError
from app.models import (
    Assessment,
    AssessmentQuestion,
    EvidenceRequest,
    ProcessStep,
    Requirement,
    SchemeRequirement,
)
from app.models.enums import AssessmentPage, AssessmentStatus
from app.repositories import AssessmentRepository

STATUS_PAGE = {
    AssessmentStatus.DRAFT_PROFILE: AssessmentPage.PROFILE,
    AssessmentStatus.PROFILE_COMPLETE: AssessmentPage.PROCESS,
    AssessmentStatus.PROCESS_COMPLETE: AssessmentPage.PROCESS,
    AssessmentStatus.EVIDENCE_PENDING: AssessmentPage.EVIDENCE,
    AssessmentStatus.EVIDENCE_COMPLETE: AssessmentPage.EVIDENCE,
    AssessmentStatus.CLARIFICATION_PENDING: AssessmentPage.CLARIFICATION,
    AssessmentStatus.READY_TO_SCORE: AssessmentPage.CLARIFICATION,
    AssessmentStatus.COMPLETED: AssessmentPage.RESULT,
    AssessmentStatus.FAILED: AssessmentPage.PROFILE,
}


def create_assessment(db: Session, *, is_sample: bool = False) -> Assessment:
    assessment = Assessment(is_sample=is_sample)
    AssessmentRepository(db).add(assessment)
    db.commit()
    return assessment


def get_assessment(db: Session, assessment_id: uuid.UUID) -> Assessment:
    return AssessmentRepository(db).get(assessment_id)


def validate_page_transition(
    assessment: Assessment, allowed_statuses: set[AssessmentStatus], operation: str
) -> None:
    if assessment.status not in allowed_statuses:
        expected = ", ".join(sorted(status.value for status in allowed_statuses))
        raise TransitionError(
            f"{operation} is not available while the assessment is "
            f"'{assessment.status.value}'. Expected: {expected}."
        )


def update_assessment_progress(assessment: Assessment, status: AssessmentStatus) -> Assessment:
    assessment.status = status
    assessment.current_page = STATUS_PAGE[status]
    return assessment


def assessment_state(db: Session, assessment: Assessment) -> dict[str, object]:
    steps = list(
        db.scalars(
            select(ProcessStep)
            .where(ProcessStep.assessment_id == assessment.id)
            .order_by(ProcessStep.position)
        )
    )
    questions = list(
        db.scalars(
            select(AssessmentQuestion)
            .where(AssessmentQuestion.assessment_id == assessment.id)
            .order_by(AssessmentQuestion.page, AssessmentQuestion.display_order)
        )
    )
    evidence_requests = list(
        db.scalars(
            select(EvidenceRequest)
            .where(EvidenceRequest.assessment_id == assessment.id)
            .order_by(EvidenceRequest.display_order)
        )
    )
    return {
        "id": assessment.id,
        "status": assessment.status,
        "current_page": assessment.current_page.value,
        "is_sample": assessment.is_sample,
        "scheme_id": assessment.scheme_id,
        "profile": assessment.profile_data,
        "process_steps": [{"position": step.position, "text": step.text} for step in steps],
        "assigned_questions": [
            {
                "id": assigned.question.id,
                "text": assigned.question.text,
                "options": assigned.question.options,
                "allows_other": assigned.question.allows_other,
                "category": assigned.question.category,
                "page": assigned.page,
                "display_order": assigned.display_order,
            }
            for assigned in questions
        ],
        "evidence_requests": serialize_evidence_requests(db, assessment, evidence_requests),
        "created_at": assessment.created_at,
        "updated_at": assessment.updated_at,
    }


def serialize_evidence_requests(
    db: Session,
    assessment: Assessment,
    requests: list[EvidenceRequest],
) -> list[dict[str, object]]:
    requirement_ids = {
        requirement_id for request in requests for requirement_id in request.requirement_ids
    }
    if assessment.scheme_id:
        requirements = list(
            db.scalars(select(SchemeRequirement).where(SchemeRequirement.id.in_(requirement_ids)))
        )
    else:
        requirements = list(
            db.scalars(select(Requirement).where(Requirement.id.in_(requirement_ids)))
        )
    description_by_id = {item.id: item.description for item in requirements}
    return [
        {
            "id": request.id,
            "evidence_type": request.evidence_type,
            "kind": request.kind,
            "title": request.title,
            "required": request.required,
            "status": request.status,
            "requirement_id": request.requirement_ids[0] if request.requirement_ids else None,
            "current_state_question": _current_state_question(request, description_by_id),
            "self_assessment": request.self_assessment,
            "display_order": request.display_order,
        }
        for request in requests
    ]


def _current_state_question(request: EvidenceRequest, description_by_id: dict[str, str]) -> str:
    descriptions = [
        description_by_id[requirement_id]
        for requirement_id in request.requirement_ids
        if requirement_id in description_by_id
    ]
    detail = " ".join(descriptions).strip()
    if detail:
        return f"Is this currently in place in your operation? {detail}"
    return f"Is this current practice in place: {request.title}?"


def clear_assessment_workflow(db: Session, assessment_id: uuid.UUID) -> None:
    db.execute(delete(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment_id))
    db.execute(delete(ProcessStep).where(ProcessStep.assessment_id == assessment_id))
    db.execute(delete(EvidenceRequest).where(EvidenceRequest.assessment_id == assessment_id))


async def load_sample_assessment(db: Session) -> Assessment:
    from app.services.sample_service import build_sample_assessment

    return await build_sample_assessment(db)
