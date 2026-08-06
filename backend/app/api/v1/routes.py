import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.assessment import (
    AssessmentCreatedResponse,
    AssessmentSummaryResponse,
    ClarificationInput,
    ClarificationPlanResponse,
    EvidenceAnalysisResponse,
    EvidencePlanResponse,
    ObservationResponse,
    ProcessAnalysisResponse,
    ProcessInput,
    ProfileInput,
    ProfileSavedResponse,
    QuestionPlanResponse,
    SampleResponse,
    StatusResponse,
    UnavailableResponse,
    UploadResponse,
)
from app.schemas.result import CompletionResponse, ResultResponse
from app.services.assessment_service import (
    assessment_state,
    create_assessment,
    get_assessment,
    load_sample_assessment,
)
from app.services.clarification_service import save_clarification_answers
from app.services.evidence_service import (
    analyze_uploaded_evidence,
    get_evidence_request,
    mark_evidence_unavailable,
    plan_final_clarifications,
    store_upload,
)
from app.services.process_service import (
    build_evidence_plan,
    extract_structured_process,
    save_adaptive_answers,
)
from app.services.profile_service import plan_adaptive_questions, save_profile_answers
from app.services.question_service import serialize_questions
from app.services.result_service import generate_result, get_result, serialize_result
from app.services.storage_service import get_storage_provider

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]


@router.get("/health", summary="Process liveness")
def health() -> dict[str, str]:
    return {"status": "ok", "service": get_settings().app_name}


@router.get("/ready", summary="Database readiness")
def ready(db: Db) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}


@router.post(
    "/assessments",
    response_model=AssessmentCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a guest assessment",
)
def create_assessment_route(db: Db) -> dict[str, object]:
    assessment = create_assessment(db)
    return {
        "id": assessment.id,
        "status": assessment.status,
        "current_page": assessment.current_page.value,
        "created_at": assessment.created_at,
    }


@router.get(
    "/assessments/{assessment_id}",
    response_model=AssessmentSummaryResponse,
    summary="Retrieve resumable assessment state",
)
def get_assessment_route(assessment_id: uuid.UUID, db: Db) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    return assessment_state(db, assessment)


@router.post(
    "/assessments/sample",
    response_model=SampleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create the completed chilli-paste demo",
)
async def sample_assessment_route(db: Db) -> dict[str, object]:
    assessment = await load_sample_assessment(db)
    return {
        "id": assessment.id,
        "status": assessment.status,
        "current_page": assessment.current_page.value,
        "result_url": f"/assessment/{assessment.id}/result",
    }


@router.put(
    "/assessments/{assessment_id}/profile",
    response_model=ProfileSavedResponse,
    summary="Save Page 1 product and business profile",
)
def save_profile_route(
    assessment_id: uuid.UUID, payload: ProfileInput, db: Db
) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    save_profile_answers(db, assessment, payload)
    return {"status": assessment.status, "profile": assessment.profile_data}


@router.post(
    "/assessments/{assessment_id}/adaptive-plan",
    response_model=QuestionPlanResponse,
    summary="Plan two to five approved adaptive questions",
)
async def adaptive_plan_route(assessment_id: uuid.UUID, db: Db) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    questions = await plan_adaptive_questions(db, assessment)
    return {"questions": serialize_questions(questions)}


@router.put(
    "/assessments/{assessment_id}/process",
    response_model=StatusResponse,
    summary="Save five process steps and adaptive answers",
)
def save_process_route(
    assessment_id: uuid.UUID, payload: ProcessInput, db: Db
) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    save_adaptive_answers(db, assessment, payload)
    return {"status": assessment.status}


@router.post(
    "/assessments/{assessment_id}/process-analysis",
    response_model=ProcessAnalysisResponse,
    summary="Extract structured manufacturing stages",
)
async def process_analysis_route(assessment_id: uuid.UUID, db: Db) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    execution = await extract_structured_process(db, assessment)
    return {
        **execution.output.model_dump(),
        "provider": execution.provider,
        "fallback_used": execution.fallback_used,
    }


@router.post(
    "/assessments/{assessment_id}/evidence-plan",
    response_model=EvidencePlanResponse,
    summary="Create the whitelisted evidence request plan",
)
def evidence_plan_route(assessment_id: uuid.UUID, db: Db) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    requests = build_evidence_plan(db, assessment)
    return {
        "status": assessment.status,
        "requests": [
            {
                "id": item.id,
                "evidence_type": item.evidence_type,
                "kind": item.kind,
                "title": item.title,
                "required": item.required,
                "status": item.status,
                "display_order": item.display_order,
            }
            for item in requests
        ],
    }


@router.post(
    "/assessments/{assessment_id}/evidence/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload one requested photo or PDF safely",
)
async def evidence_upload_route(
    assessment_id: uuid.UUID,
    db: Db,
    evidence_request_id: Annotated[uuid.UUID, Form()],
    file: Annotated[UploadFile, File(description="JPEG, PNG, WebP, or requested PDF")],
) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    evidence_request = get_evidence_request(db, assessment_id, evidence_request_id)
    config = get_settings()
    hard_limit = max(config.max_image_mb, config.max_pdf_mb) * 1024 * 1024 + 1
    data = await file.read(hard_limit)
    stored = store_upload(
        db,
        assessment,
        evidence_request,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        data=data,
        storage=get_storage_provider(),
    )
    return {
        "file_id": stored.id,
        "evidence_request_id": evidence_request.id,
        "status": evidence_request.status,
        "content_type": stored.content_type,
        "size_bytes": stored.size_bytes,
    }


@router.put(
    "/assessments/{assessment_id}/evidence/{evidence_request_id}/unavailable",
    response_model=UnavailableResponse,
    summary="Mark a requested evidence item unavailable",
)
def evidence_unavailable_route(
    assessment_id: uuid.UUID, evidence_request_id: uuid.UUID, db: Db
) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    evidence_request = get_evidence_request(db, assessment_id, evidence_request_id)
    mark_evidence_unavailable(db, assessment, evidence_request)
    return {"evidence_request_id": evidence_request.id, "status": evidence_request.status}


@router.post(
    "/assessments/{assessment_id}/evidence-analysis",
    response_model=EvidenceAnalysisResponse,
    summary="Analyze resolved evidence as cautious observations",
)
async def evidence_analysis_route(assessment_id: uuid.UUID, db: Db) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    analysis = await analyze_uploaded_evidence(db, assessment, get_storage_provider())
    return {
        "status": assessment.status,
        "provider": analysis.execution.provider,
        "fallback_used": analysis.execution.fallback_used,
        "observations": [
            ObservationResponse(
                id=item.id,
                evidence_request_id=item.evidence_request_id,
                requirement_id=item.requirement_id,
                polarity=item.polarity.value,
                text=item.text,
                confidence=float(item.confidence),
            )
            for item in analysis.observations
        ],
    }


@router.post(
    "/assessments/{assessment_id}/clarification-plan",
    response_model=ClarificationPlanResponse,
    summary="Plan three to five approved final questions",
)
async def clarification_plan_route(assessment_id: uuid.UUID, db: Db) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    questions = await plan_final_clarifications(db, assessment)
    return {
        "status": assessment.status,
        "questions": serialize_questions(questions),
    }


@router.put(
    "/assessments/{assessment_id}/clarifications",
    response_model=StatusResponse,
    summary="Save final clarification answers",
)
def clarification_answers_route(
    assessment_id: uuid.UUID, payload: ClarificationInput, db: Db
) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    save_clarification_answers(db, assessment, payload)
    return {"status": assessment.status}


@router.post(
    "/assessments/{assessment_id}/complete",
    response_model=CompletionResponse,
    summary="Run deterministic scoring and roadmap generation",
)
async def complete_route(assessment_id: uuid.UUID, db: Db) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    result = await generate_result(db, assessment)
    from app.models import RoadmapItem

    roadmap_count = len(
        list(db.scalars(select(RoadmapItem.id).where(RoadmapItem.result_id == result.id)))
    )
    return {
        "status": assessment.status.value,
        "result": {
            "overall_score_raw": result.overall_score_raw,
            "overall_score": result.overall_score,
            "evidence_completeness": result.evidence_completeness,
            "roadmap_count": roadmap_count,
        },
    }


@router.get(
    "/assessments/{assessment_id}/result",
    response_model=ResultResponse,
    summary="Retrieve the stored explainable readiness result",
)
def result_route(assessment_id: uuid.UUID, db: Db) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    result = get_result(db, assessment)
    return serialize_result(db, assessment, result)
