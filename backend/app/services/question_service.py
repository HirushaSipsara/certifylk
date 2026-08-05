from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import AssessmentAnswer, AssessmentQuestion, QuestionBank
from app.models.enums import QuestionPage
from app.schemas.assessment import AnswerInput


def validate_and_save_assigned_answers(
    db: Session,
    *,
    assessment_id: object,
    page: QuestionPage,
    answers: list[AnswerInput],
) -> None:
    assigned = list(
        db.scalars(
            select(AssessmentQuestion)
            .where(AssessmentQuestion.assessment_id == assessment_id)
            .where(AssessmentQuestion.page == page)
        )
    )
    assigned_by_id = {item.question_id: item for item in assigned}
    provided = {item.question_id for item in answers}
    if provided != set(assigned_by_id):
        raise AppError(
            "invalid_answers",
            "Answer every assigned question and do not submit unassigned questions.",
            422,
        )
    db.execute(
        delete(AssessmentAnswer)
        .where(AssessmentAnswer.assessment_id == assessment_id)
        .where(AssessmentAnswer.page == page.value)
    )
    now = datetime.now(timezone.utc)
    for answer in answers:
        assignment = assigned_by_id[answer.question_id]
        question = assignment.question
        option_values = {option["value"] for option in question.options}
        if answer.value == "other":
            if not question.allows_other or not (answer.other_text or "").strip():
                raise AppError(
                    "invalid_other_answer", f"{answer.question_id} requires Other details.", 422
                )
            value: object = {
                "value": "other",
                "other_text": (answer.other_text or "").strip(),
            }
        elif answer.value not in option_values:
            raise AppError(
                "invalid_answer_option",
                f"'{answer.value}' is not an approved option for {answer.question_id}.",
                422,
            )
        else:
            value = answer.value
        db.add(
            AssessmentAnswer(
                assessment_id=assessment_id,
                page=page.value,
                key=answer.question_id,
                value=value,
                created_at=now,
            )
        )
        assignment.answered = True


def get_answer_map(db: Session, assessment_id: object) -> dict[str, str]:
    answers = list(
        db.scalars(select(AssessmentAnswer).where(AssessmentAnswer.assessment_id == assessment_id))
    )
    output: dict[str, str] = {}
    for answer in answers:
        if isinstance(answer.value, dict):
            output[answer.key] = str(answer.value.get("value", "other"))
        else:
            output[answer.key] = str(answer.value)
    return output


def serialize_questions(questions: list[QuestionBank]) -> list[dict[str, object]]:
    return [
        {
            "id": question.id,
            "text": question.text,
            "options": question.options,
            "allows_other": question.allows_other,
            "category": question.category,
        }
        for question in questions
    ]
