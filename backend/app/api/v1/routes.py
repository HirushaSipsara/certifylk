import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.enums import CertificationTrack
from app.schemas.assessment import (
    ApplicabilityResponse,
    AssessmentCreatedResponse,
    AssessmentSummaryResponse,
    BusinessProfileInput,
    BusinessProfileResponse,
    CategoryResponse,
    ClarificationInput,
    ClarificationPlanResponse,
    EvidenceAnalysisResponse,
    EvidenceExpectationResponse,
    EvidencePlanResponse,
    ObservationResponse,
    ProcessAnalysisResponse,
    ProcessInput,
    ProductResponse,
    ProfileInput,
    ProfileSavedResponse,
    QuestionPlanResponse,
    SampleResponse,
    SchemeChipResponse,
    SchemeRequirementResponse,
    StatusResponse,
    UnavailableResponse,
    UploadResponse,
)
from app.schemas.result import CompletionResponse, ResultResponse
from app.services.applicability_service import create_business_profile, run_applicability_agent
from app.services.assessment_service import (
    assessment_state,
    create_assessment,
    get_assessment,
    load_sample_assessment,
)
from app.services.catalog_service import (
    get_evidence_expectations,
    get_scheme_requirements,
    has_unverified_requirements,
    list_categories,
    list_products,
    list_schemes,
)
from app.services.clarification_service import save_clarification_answers
from app.services.evidence_service import (
    analyze_uploaded_evidence,
    get_evidence_request,
    mark_evidence_unavailable,
    plan_final_clarifications,
    reset_evidence_request,
    store_upload,
)
from app.services.process_service import (
    build_evidence_plan,
    extract_structured_process,
    save_adaptive_answers,
)
from app.services.profile_service import plan_adaptive_questions, save_profile_answers
from app.services.question_service import serialize_questions
from app.services.result_service import (
    generate_result,
    generate_scheme_result,
    get_result,
    serialize_result,
)
from app.services.storage_service import get_storage_provider

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]


@router.get("/health", summary="Process liveness")
def health() -> dict[str, str]:
    settings = get_settings()
    sha = (
        settings.release_sha
        if settings.release_sha != "unknown"
        else os.getenv("IMAGE_TAG", "unknown")
    )
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.api_version,
        "release_sha": sha[:40] if sha else "unknown",
    }


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
    summary="Create the completed Fresh Fruit Cordial demo",
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
    mark_evidence_unavailable(db, assessment, evidence_request, storage=get_storage_provider())
    return {"evidence_request_id": evidence_request.id, "status": evidence_request.status}


@router.delete(
    "/assessments/{assessment_id}/evidence/{evidence_request_id}",
    response_model=UnavailableResponse,
    summary="Reset an uploaded or unavailable evidence item so it can be re-uploaded",
)
def evidence_reset_route(
    assessment_id: uuid.UUID, evidence_request_id: uuid.UUID, db: Db
) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    evidence_request = get_evidence_request(db, assessment_id, evidence_request_id)
    reset_evidence_request(db, assessment, evidence_request, get_storage_provider())
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
    result = (
        await generate_scheme_result(db, assessment)
        if assessment.scheme_id
        else await generate_result(db, assessment)
    )
    from app.models import RoadmapItem

    roadmap_count = (
        len(result.roadmap_snapshot)
        if result.roadmap_snapshot
        else len(list(db.scalars(select(RoadmapItem.id).where(RoadmapItem.result_id == result.id))))
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


# ── Certification knowledge base routes ───────────────────────────────────────


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="List enabled food product categories",
)
def list_categories_route(db: Db) -> list[dict[str, object]]:
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "display_order": cat.display_order,
        }
        for cat in list_categories(db)
    ]


@router.get(
    "/categories/{category_id}/products",
    response_model=list[ProductResponse],
    summary="List enabled products for a category",
)
def list_products_route(category_id: str, db: Db) -> list[dict[str, object]]:
    return [
        {
            "id": prod.id,
            "name": prod.name,
            "slug": prod.slug,
            "description": prod.description,
            "category_id": prod.category_id,
            "display_order": prod.display_order,
        }
        for prod in list_products(db, category_id)
    ]


@router.get(
    "/schemes",
    response_model=list[SchemeChipResponse],
    summary="List certification schemes, optionally filtered by track",
)
def list_schemes_route(
    db: Db,
    track: str | None = Query(default=None, description="product_quality or process_management"),
) -> list[dict[str, object]]:
    track_enum = None
    if track:
        try:
            track_enum = CertificationTrack(track)
        except ValueError:
            pass
    schemes = list_schemes(db, track_enum)
    return [
        {
            "id": s.id,
            "name": s.name,
            "short_code": s.short_code,
            "track": s.track.value if hasattr(s.track, "value") else str(s.track),
            "mandatory_tier": s.mandatory_tier.value
            if hasattr(s.mandatory_tier, "value")
            else str(s.mandatory_tier),
            "standard_version": s.standard_version,
            "catalogue_revision": s.catalogue_revision,
            "summary": s.summary,
            "typical_timeline_days": s.typical_timeline_days,
            "body_name": s.body.name if s.body else "",
            "active": s.active,
        }
        for s in schemes
    ]


@router.get(
    "/schemes/{scheme_id}/requirements",
    response_model=list[SchemeRequirementResponse],
    summary="List requirements for a specific certification scheme",
)
def scheme_requirements_route(scheme_id: str, db: Db) -> list[dict[str, object]]:
    reqs = get_scheme_requirements(db, scheme_id)
    return [
        {
            "id": r.id,
            "scheme_id": r.scheme_id,
            "category_label": r.category_label,
            "title": r.title,
            "description": r.description,
            "weight": float(r.weight),
            "safety_critical": r.safety_critical,
            "source_document": r.source_document,
            "source_document_id": r.source_document_id,
            "clause_reference": r.clause_reference,
            "source_url": r.source_url,
            "content_verified": r.content_verified,
            "standard_version": r.standard_version,
            "effective_date": r.effective_date.isoformat() if r.effective_date else None,
            "display_order": r.display_order,
        }
        for r in reqs
    ]


@router.get(
    "/schemes/{scheme_id}/evidence-expectations",
    response_model=list[EvidenceExpectationResponse],
    summary="List evidence expectations for a specific certification scheme",
)
def scheme_evidence_expectations_route(scheme_id: str, db: Db) -> list[dict[str, object]]:
    expectations = get_evidence_expectations(db, scheme_id)
    return [
        {
            "id": item.id,
            "scheme_id": item.scheme_id,
            "requirement_id": item.requirement_id,
            "kind": item.kind,
            "label": item.label,
            "guidance_text": item.guidance_text,
            "required": item.required,
            "display_order": item.display_order,
        }
        for item in expectations
    ]


@router.post(
    "/business-profiles",
    response_model=BusinessProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a business profile and optionally link to an assessment",
)
async def create_business_profile_route(payload: BusinessProfileInput, db: Db) -> dict[str, object]:
    from app.services.catalog_service import get_product_by_slug

    profile = create_business_profile(
        db,
        name=payload.name,
        business_type=payload.business_type,
        years_operating=payload.years_operating,
        scale=payload.scale,
        market=payload.market,
        existing_certifications=payload.existing_certifications,
        has_food_licence=payload.has_food_licence,
        monthly_volume_range=payload.monthly_volume_range,
        additional_info=payload.additional_info,
    )

    # Optionally link to an existing assessment
    if payload.assessment_id:
        assessment = get_assessment(db, payload.assessment_id)
        assessment.business_profile_id = profile.id
        # Link product if a slug was supplied
        if payload.product_slug:
            product = get_product_by_slug(db, payload.product_slug)
            if product:
                assessment.product_id = product.id
        # Advance assessment page and status once profile is attached
        from app.models.enums import AssessmentPage, AssessmentStatus

        assessment.current_page = AssessmentPage.PROCESS
        if assessment.status == AssessmentStatus.DRAFT_PROFILE:
            assessment.status = AssessmentStatus.PROFILE_COMPLETE
        db.flush()

    db.commit()
    return {
        "id": profile.id,
        "name": profile.name,
        "business_type": profile.business_type,
        "scale": profile.scale,
        "market": profile.market,
        "has_food_licence": profile.has_food_licence,
    }


@router.post(
    "/assessments/{assessment_id}/applicable-schemes",
    response_model=ApplicabilityResponse,
    summary="Run the Applicability Reasoning Agent for this assessment",
)
async def applicable_schemes_route(assessment_id: uuid.UUID, db: Db) -> dict[str, object]:
    assessment = get_assessment(db, assessment_id)
    decision = await run_applicability_agent(db, assessment)

    # Build enriched response with scheme metadata
    from app.services.catalog_service import get_scheme

    decision_responses = []
    for d in decision.decisions:
        scheme = get_scheme(db, d.scheme_id)
        decision_responses.append(
            {
                "scheme_id": d.scheme_id,
                "tier": d.tier,
                "confidence": d.confidence,
                "reasoning": d.reasoning,
                "source_reference": d.source_reference,
                "scheme_name": scheme.name if scheme else d.scheme_id,
                "body_name": scheme.body.name if scheme and scheme.body else "",
                "typical_timeline_days": scheme.typical_timeline_days if scheme else None,
                "summary": scheme.summary if scheme else "",
            }
        )

    any_unverified = (
        has_unverified_requirements(db, assessment.scheme_id) if assessment.scheme_id else False
    )

    db.commit()
    return {
        "assessment_id": assessment.id,
        "overall_reasoning": decision.overall_reasoning,
        "recommended_path_scheme_id": decision.recommended_path_scheme_id,
        "decisions": decision_responses,
        "provider": assessment.profile_data.get("applicability_decision", {}).get(
            "provider", "mock"
        ),
        "fallback_used": assessment.profile_data.get("applicability_decision", {}).get(
            "fallback_used", False
        ),
        "has_unverified_content": any_unverified,
    }


@router.get(
    "/assessments/{assessment_id}/scheme-requirements",
    response_model=list[SchemeRequirementResponse],
    summary="List scheme requirements for this assessment (based on linked scheme)",
)
def assessment_scheme_requirements_route(
    assessment_id: uuid.UUID, db: Db
) -> list[dict[str, object]]:
    assessment = get_assessment(db, assessment_id)
    if not assessment.scheme_id:
        return []
    reqs = get_scheme_requirements(db, assessment.scheme_id)
    return [
        {
            "id": r.id,
            "scheme_id": r.scheme_id,
            "category_label": r.category_label,
            "title": r.title,
            "description": r.description,
            "weight": float(r.weight),
            "safety_critical": r.safety_critical,
            "source_document": r.source_document,
            "source_document_id": r.source_document_id,
            "clause_reference": r.clause_reference,
            "source_url": r.source_url,
            "content_verified": r.content_verified,
            "standard_version": r.standard_version,
            "effective_date": r.effective_date.isoformat() if r.effective_date else None,
            "display_order": r.display_order,
        }
        for r in reqs
    ]
