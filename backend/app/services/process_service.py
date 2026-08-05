from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai import AIProvider
from app.data.catalog import EVIDENCE_TYPES
from app.models import Assessment, EvidenceRequest, ProcessStep
from app.models.enums import (
    AssessmentStatus,
    EvidenceKind,
    EvidenceRequestStatus,
    QuestionPage,
)
from app.schemas.ai import ProcessExtractionOutput
from app.schemas.assessment import ProcessInput
from app.services.ai_service import run_with_validation
from app.services.assessment_service import update_assessment_progress, validate_page_transition
from app.services.question_service import get_answer_map, validate_and_save_assigned_answers


def save_process_steps(db: Session, assessment: Assessment, steps: list[str]) -> None:
    db.execute(delete(ProcessStep).where(ProcessStep.assessment_id == assessment.id))
    for position, text in enumerate(steps, start=1):
        db.add(ProcessStep(assessment_id=assessment.id, position=position, text=text))


def save_adaptive_answers(db: Session, assessment: Assessment, payload: ProcessInput) -> Assessment:
    validate_page_transition(assessment, {AssessmentStatus.PROFILE_COMPLETE}, "Process submission")
    save_process_steps(db, assessment, payload.steps)
    validate_and_save_assigned_answers(
        db,
        assessment_id=assessment.id,
        page=QuestionPage.ADAPTIVE,
        answers=payload.adaptive_answers,
    )
    update_assessment_progress(assessment, AssessmentStatus.PROCESS_COMPLETE)
    db.commit()
    return assessment


def derive_process_tags(stages: list[dict[str, object]]) -> list[str]:
    tags: list[str] = []
    for stage in stages:
        raw_tags = stage.get("tags", [])
        if isinstance(raw_tags, list):
            tags.extend(str(tag) for tag in raw_tags)
    return list(dict.fromkeys(tags))


async def extract_structured_process(
    db: Session, assessment: Assessment
) -> ProcessExtractionOutput:
    validate_page_transition(assessment, {AssessmentStatus.PROCESS_COMPLETE}, "Process analysis")
    steps = list(
        db.scalars(
            select(ProcessStep)
            .where(ProcessStep.assessment_id == assessment.id)
            .order_by(ProcessStep.position)
        )
    )
    answers = get_answer_map(db, assessment.id)

    async def call(provider: AIProvider) -> ProcessExtractionOutput:
        return await provider.extract_process([step.text for step in steps], answers)

    output = await run_with_validation(db, assessment.id, "extract_process", call)
    step_by_position = {step.position: step for step in steps}
    for stage in output.stages:
        step = step_by_position[stage.position]
        step.normalized_name = stage.name
        step.tags = [str(tag) for tag in stage.tags]
        step.confidence = Decimal(str(stage.confidence))
    assessment.process_analysis = output.model_dump()
    db.commit()
    return output


def build_evidence_plan(db: Session, assessment: Assessment) -> list[EvidenceRequest]:
    validate_page_transition(assessment, {AssessmentStatus.PROCESS_COMPLETE}, "Evidence planning")
    if not assessment.process_analysis.get("stages"):
        from app.core.errors import TransitionError

        raise TransitionError("Run process analysis before creating an evidence plan.")
    photo_types = [
        "production_area",
        "handwashing_area",
        "ingredient_storage",
        "packaging_area",
        "finished_product_label_photo",
    ]
    if assessment.profile_data.get("storage_method") in {"refrigerated", "frozen", "mixed"}:
        photo_types[-1] = "cold_storage"
    document_types = ["product_label", "production_record"]
    planned_types = photo_types[:5] + document_types[:2]
    db.execute(delete(EvidenceRequest).where(EvidenceRequest.assessment_id == assessment.id))
    requests: list[EvidenceRequest] = []
    for order, evidence_type in enumerate(planned_types, start=1):
        definition = EVIDENCE_TYPES[evidence_type]
        request = EvidenceRequest(
            assessment_id=assessment.id,
            evidence_type=evidence_type,
            kind=EvidenceKind(str(definition["kind"])),
            title=str(definition["title"]),
            requirement_ids=list(definition["requirements"]),
            required=False,
            status=EvidenceRequestStatus.REQUESTED,
            display_order=order,
        )
        db.add(request)
        requests.append(request)
    update_assessment_progress(assessment, AssessmentStatus.EVIDENCE_PENDING)
    db.commit()
    return requests
