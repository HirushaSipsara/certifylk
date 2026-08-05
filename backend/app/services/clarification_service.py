from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import TransitionError
from app.models import Assessment, AssessmentQuestion
from app.models.enums import AssessmentStatus, QuestionPage
from app.schemas.assessment import ClarificationInput
from app.services.assessment_service import update_assessment_progress, validate_page_transition
from app.services.evidence_service import plan_final_clarifications
from app.services.question_service import validate_and_save_assigned_answers


def save_clarification_answers(
    db: Session, assessment: Assessment, payload: ClarificationInput
) -> Assessment:
    validate_page_transition(
        assessment,
        {AssessmentStatus.CLARIFICATION_PENDING},
        "Clarification submission",
    )
    validate_and_save_assigned_answers(
        db,
        assessment_id=assessment.id,
        page=QuestionPage.CLARIFICATION,
        answers=payload.answers,
    )
    update_assessment_progress(assessment, AssessmentStatus.READY_TO_SCORE)
    db.commit()
    return assessment


def check_assessment_completeness(db: Session, assessment: Assessment) -> bool:
    if assessment.status != AssessmentStatus.READY_TO_SCORE:
        return False
    total, answered = db.execute(
        select(
            func.count(AssessmentQuestion.id),
            func.count(AssessmentQuestion.id).filter(AssessmentQuestion.answered.is_(True)),
        ).where(
            AssessmentQuestion.assessment_id == assessment.id,
            AssessmentQuestion.page == QuestionPage.CLARIFICATION,
        )
    ).one()
    return bool(total and total == answered)


def ensure_assessment_complete(db: Session, assessment: Assessment) -> None:
    if not check_assessment_completeness(db, assessment):
        raise TransitionError("Answer all final clarification questions before scoring.")


__all__ = [
    "check_assessment_completeness",
    "ensure_assessment_complete",
    "plan_final_clarifications",
    "save_clarification_answers",
]
