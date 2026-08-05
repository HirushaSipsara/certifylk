from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Assessment, QuestionBank, Requirement
from app.schemas.assessment import AnswerInput, ClarificationInput, ProcessInput, ProfileInput
from app.services.assessment_service import create_assessment
from app.services.clarification_service import save_clarification_answers
from app.services.evidence_service import (
    analyze_uploaded_evidence,
    mark_evidence_unavailable,
    plan_final_clarifications,
)
from app.services.process_service import (
    build_evidence_plan,
    extract_structured_process,
    save_adaptive_answers,
)
from app.services.profile_service import plan_adaptive_questions, save_profile_answers
from app.services.result_service import generate_result
from app.services.seed_service import seed_catalogue
from app.storage import LocalStorageProvider

SAMPLE_ANSWERS = {
    "HYG_HAND_01": "always",
    "HYG_CLEAN_01": "routine_no_record",
    "HYG_CHEM_01": "separate_area",
    "HYG_PEST_01": "checked_not_logged",
    "PROC_TEMP_01": "appearance_only",
    "PROC_THERM_01": "none",
    "PROC_SEP_01": "clean_between",
    "DOC_BATCH_01": "sometimes",
    "DOC_CLEAN_01": "sometimes",
    "SUP_SOURCE_01": "known_variable",
    "SUP_REG_01": "none",
    "SUP_CHECK_01": "check_no_record",
    "PACK_LABEL_01": "some_details",
    "PACK_GRADE_01": "none",
    "PACK_FILL_01": "cleaned_shared_area",
    "STORE_RAISED_01": "raised_closed",
    "STORE_FIN_01": "shared_protected",
    "TRACE_CODE_01": "none",
    "TRACE_SALES_01": "sales_only",
}


def _answers_for_questions(questions: list[QuestionBank]) -> list[AnswerInput]:
    answers: list[AnswerInput] = []
    for question in questions:
        value = SAMPLE_ANSWERS.get(question.id, question.options[0]["value"])
        answers.append(AnswerInput(question_id=question.id, value=value))
    return answers


async def build_sample_assessment(db: Session) -> Assessment:
    if not db.scalar(select(func.count(Requirement.id))):
        seed_catalogue(db)
    assessment = create_assessment(db, is_sample=True)
    profile = ProfileInput(
        product_name="Homemade chilli paste",
        food_category="processed_food",
        production_location="home_kitchen",
        production_scale="small",
        worker_range="1_5",
        packaging_type="glass_bottle",
        storage_method="room_temperature",
        shelf_life_range="one_to_six_months",
        existing_certification="none",
        production_record_frequency="sometimes",
        additional_information="Cooked in small batches and filled manually.",
    )
    save_profile_answers(db, assessment, profile)
    adaptive = await plan_adaptive_questions(db, assessment)
    process = ProcessInput(
        steps=[
            "Purchase chillies and ingredients.",
            "Wash and prepare ingredients.",
            "Cook the mixture.",
            "Fill glass bottles manually.",
            "Store and distribute.",
        ],
        adaptive_answers=_answers_for_questions(adaptive),
    )
    save_adaptive_answers(db, assessment, process)
    await extract_structured_process(db, assessment)
    requests = build_evidence_plan(db, assessment)
    for request in requests:
        mark_evidence_unavailable(db, assessment, request)
    await analyze_uploaded_evidence(db, assessment, LocalStorageProvider(get_settings().upload_dir))
    clarifications = await plan_final_clarifications(db, assessment)
    save_clarification_answers(
        db,
        assessment,
        ClarificationInput(answers=_answers_for_questions(clarifications)),
    )
    await generate_result(db, assessment)
    return assessment
