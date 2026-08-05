from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai import AIProvider
from app.models import Assessment, AssessmentAnswer, AssessmentQuestion, QuestionBank
from app.models.enums import AssessmentPage, AssessmentStatus, QuestionPage
from app.schemas.ai import QuestionPlanOutput
from app.schemas.assessment import ProfileInput
from app.services.ai_service import run_with_validation, validate_question_plan
from app.services.assessment_service import update_assessment_progress, validate_page_transition


def save_profile_answers(db: Session, assessment: Assessment, profile: ProfileInput) -> Assessment:
    validate_page_transition(
        assessment,
        {AssessmentStatus.DRAFT_PROFILE, AssessmentStatus.PROFILE_COMPLETE},
        "Profile submission",
    )
    data = profile.model_dump()
    assessment.profile_data = data
    db.execute(
        delete(AssessmentAnswer)
        .where(AssessmentAnswer.assessment_id == assessment.id)
        .where(AssessmentAnswer.page == "profile")
    )
    now = datetime.now(timezone.utc)
    for key, value in data.items():
        db.add(
            AssessmentAnswer(
                assessment_id=assessment.id,
                page="profile",
                key=key,
                value=value,
                created_at=now,
            )
        )
    update_assessment_progress(assessment, AssessmentStatus.PROFILE_COMPLETE)
    db.commit()
    return assessment


def build_profile_summary(assessment: Assessment) -> dict[str, object]:
    profile = assessment.profile_data
    return {
        "product": profile.get("product_name"),
        "category": profile.get("food_category"),
        "location": profile.get("production_location"),
        "packaging": profile.get("packaging_type"),
        "storage": profile.get("storage_method"),
        "records": profile.get("production_record_frequency"),
    }


def generate_candidate_questions(db: Session, assessment: Assessment) -> list[QuestionBank]:
    questions = list(
        db.scalars(
            select(QuestionBank)
            .where(QuestionBank.active.is_(True))
            .order_by(QuestionBank.priority.desc(), QuestionBank.id)
        )
    )
    product_tag = str(assessment.profile_data.get("food_category", "processed_food"))
    return [
        question
        for question in questions
        if "adaptive" in question.page_eligibility
        and (not question.product_tags or product_tag in question.product_tags)
    ]


async def plan_adaptive_questions(db: Session, assessment: Assessment) -> list[QuestionBank]:
    validate_page_transition(
        assessment, {AssessmentStatus.PROFILE_COMPLETE}, "Adaptive question planning"
    )
    candidates = generate_candidate_questions(db, assessment)
    candidate_ids = [item.id for item in candidates]

    async def call(provider: AIProvider) -> QuestionPlanOutput:
        return await provider.plan_adaptive_questions(
            build_profile_summary(assessment), candidate_ids
        )

    output = await run_with_validation(
        db,
        assessment.id,
        "plan_adaptive_questions",
        call,
        lambda result: validate_question_plan(result, candidate_ids, 2, 5),
    )
    selected_by_id = {item.id: item for item in candidates}
    db.execute(
        delete(AssessmentQuestion)
        .where(AssessmentQuestion.assessment_id == assessment.id)
        .where(AssessmentQuestion.page == QuestionPage.ADAPTIVE)
    )
    now = datetime.now(timezone.utc)
    selected = [selected_by_id[item] for item in output.question_ids]
    for order, question in enumerate(selected, start=1):
        db.add(
            AssessmentQuestion(
                assessment_id=assessment.id,
                question_id=question.id,
                page=QuestionPage.ADAPTIVE,
                display_order=order,
                planning_rationale=output.reason,
                answered=False,
                created_at=now,
            )
        )
    assessment.current_page = AssessmentPage.PROCESS
    db.commit()
    return selected
