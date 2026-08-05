import base64
import hashlib
import io
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai import AIProvider
from app.core.errors import NotFoundError, TransitionError
from app.models import (
    Assessment,
    AssessmentQuestion,
    EvidenceFile,
    EvidenceObservation,
    EvidenceRequest,
    QuestionBank,
)
from app.models.enums import (
    AssessmentStatus,
    EvidenceRequestStatus,
    ObservationPolarity,
    QuestionPage,
)
from app.schemas.ai import EvidenceAnalysisOutput, EvidenceInput, QuestionPlanOutput
from app.services.ai_service import (
    run_with_validation,
    validate_evidence_output,
    validate_question_plan,
    wrap_untrusted_evidence_data,
)
from app.services.assessment_service import update_assessment_progress, validate_page_transition
from app.services.storage_service import (
    generate_safe_storage_key,
    sanitize_original_filename,
    validate_upload,
)
from app.storage import StorageProvider


def get_evidence_request(
    db: Session, assessment_id: uuid.UUID, evidence_request_id: uuid.UUID
) -> EvidenceRequest:
    request = db.scalar(
        select(EvidenceRequest)
        .where(EvidenceRequest.id == evidence_request_id)
        .where(EvidenceRequest.assessment_id == assessment_id)
    )
    if request is None:
        raise NotFoundError("Evidence request not found.")
    return request


def store_upload(
    db: Session,
    assessment: Assessment,
    request: EvidenceRequest,
    *,
    filename: str,
    content_type: str,
    data: bytes,
    storage: StorageProvider,
) -> EvidenceFile:
    validate_page_transition(assessment, {AssessmentStatus.EVIDENCE_PENDING}, "Evidence upload")
    if request.status != EvidenceRequestStatus.REQUESTED:
        raise TransitionError("This evidence request has already been resolved.")
    extension = validate_upload(
        filename=filename,
        content_type=content_type,
        data=data,
        kind=request.kind,
    )
    key = generate_safe_storage_key(storage, assessment.id, request.id, extension)
    storage.save_file(key, io.BytesIO(data))
    evidence_file = EvidenceFile(
        assessment_id=assessment.id,
        evidence_request_id=request.id,
        storage_key=key,
        original_name=sanitize_original_filename(filename),
        content_type=content_type,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        created_at=datetime.now(timezone.utc),
    )
    try:
        db.add(evidence_file)
        request.status = EvidenceRequestStatus.UPLOADED
        db.commit()
    except Exception:
        db.rollback()
        storage.delete_file(key)
        raise
    return evidence_file


def mark_evidence_unavailable(
    db: Session, assessment: Assessment, request: EvidenceRequest
) -> EvidenceRequest:
    validate_page_transition(
        assessment, {AssessmentStatus.EVIDENCE_PENDING}, "Mark evidence unavailable"
    )
    if request.status != EvidenceRequestStatus.REQUESTED:
        raise TransitionError("This evidence request has already been resolved.")
    request.status = EvidenceRequestStatus.UNAVAILABLE
    db.commit()
    return request


async def analyze_uploaded_evidence(
    db: Session,
    assessment: Assessment,
    storage: StorageProvider,
) -> list[EvidenceObservation]:
    validate_page_transition(assessment, {AssessmentStatus.EVIDENCE_PENDING}, "Evidence analysis")
    requests = list(
        db.scalars(
            select(EvidenceRequest)
            .where(EvidenceRequest.assessment_id == assessment.id)
            .order_by(EvidenceRequest.display_order)
        )
    )
    if any(request.status == EvidenceRequestStatus.REQUESTED for request in requests):
        raise TransitionError("Resolve every evidence request before analysis.")
    files = list(
        db.scalars(select(EvidenceFile).where(EvidenceFile.assessment_id == assessment.id))
    )
    file_by_request = {item.evidence_request_id: item for item in files}
    evidence_inputs: list[EvidenceInput] = []
    for request in requests:
        evidence_file = file_by_request.get(request.id)
        if evidence_file is None:
            continue
        with storage.open_file(evidence_file.storage_key) as source:
            data = source.read()
        evidence_inputs.append(
            EvidenceInput(
                request_id=request.id,
                evidence_type=request.evidence_type,
                requirement_ids=request.requirement_ids,
                content_type=evidence_file.content_type,
                safe_data_summary=wrap_untrusted_evidence_data(
                    f"Stored {request.title}; original content is attached as binary evidence."
                ),
                data_base64=base64.b64encode(data).decode("ascii"),
            )
        )
    allowed_requirements = {
        requirement_id for request in requests for requirement_id in request.requirement_ids
    }
    request_ids = {request.id for request in requests}

    async def call(provider: AIProvider) -> EvidenceAnalysisOutput:
        return await provider.analyze_evidence(evidence_inputs, allowed_requirements)

    output = await run_with_validation(
        db,
        assessment.id,
        "analyze_evidence",
        call,
        lambda result: validate_evidence_output(result, request_ids, allowed_requirements),
    )
    observations = merge_evidence_observations(db, assessment.id, output, file_by_request)
    for request in requests:
        if request.status == EvidenceRequestStatus.UPLOADED:
            request.status = EvidenceRequestStatus.ANALYZED
    update_assessment_progress(assessment, AssessmentStatus.EVIDENCE_COMPLETE)
    db.commit()
    return observations


def merge_evidence_observations(
    db: Session,
    assessment_id: uuid.UUID,
    output: EvidenceAnalysisOutput,
    file_by_request: dict[uuid.UUID, EvidenceFile],
) -> list[EvidenceObservation]:
    db.execute(
        delete(EvidenceObservation).where(EvidenceObservation.assessment_id == assessment_id)
    )
    observations: list[EvidenceObservation] = []
    now = datetime.now(timezone.utc)
    for item in output.observations:
        evidence_file = file_by_request.get(item.evidence_request_id)
        observation = EvidenceObservation(
            assessment_id=assessment_id,
            evidence_request_id=item.evidence_request_id,
            evidence_file_id=evidence_file.id if evidence_file else None,
            requirement_id=item.requirement_id,
            polarity=ObservationPolarity(item.polarity),
            text=item.text,
            confidence=item.confidence,
            provider="validated_ai",
            created_at=now,
        )
        db.add(observation)
        observations.append(observation)
    db.flush()
    return observations


def build_clarification_candidates(db: Session, assessment: Assessment) -> list[QuestionBank]:
    assigned_ids = set(
        db.scalars(
            select(AssessmentQuestion.question_id).where(
                AssessmentQuestion.assessment_id == assessment.id
            )
        )
    )
    questions = list(
        db.scalars(
            select(QuestionBank)
            .where(QuestionBank.active.is_(True))
            .order_by(QuestionBank.priority.desc(), QuestionBank.id)
        )
    )
    return [
        question
        for question in questions
        if "clarification" in question.page_eligibility and question.id not in assigned_ids
    ]


async def plan_final_clarifications(db: Session, assessment: Assessment) -> list[QuestionBank]:
    validate_page_transition(
        assessment, {AssessmentStatus.EVIDENCE_COMPLETE}, "Clarification planning"
    )
    candidates = build_clarification_candidates(db, assessment)
    candidate_ids = [question.id for question in candidates]
    context = {
        "profile": assessment.profile_data,
        "process_uncertainties": assessment.process_analysis.get("uncertainties", []),
    }

    async def call(provider: AIProvider) -> QuestionPlanOutput:
        return await provider.plan_clarifications(context, candidate_ids)

    output = await run_with_validation(
        db,
        assessment.id,
        "plan_clarifications",
        call,
        lambda result: validate_question_plan(result, candidate_ids, 3, 5),
    )
    db.execute(
        delete(AssessmentQuestion)
        .where(AssessmentQuestion.assessment_id == assessment.id)
        .where(AssessmentQuestion.page == QuestionPage.CLARIFICATION)
    )
    by_id = {question.id: question for question in candidates}
    selected = [by_id[question_id] for question_id in output.question_ids]
    now = datetime.now(timezone.utc)
    for order, question in enumerate(selected, start=1):
        db.add(
            AssessmentQuestion(
                assessment_id=assessment.id,
                question_id=question.id,
                page=QuestionPage.CLARIFICATION,
                display_order=order,
                planning_rationale=output.reason,
                answered=False,
                created_at=now,
            )
        )
    update_assessment_progress(assessment, AssessmentStatus.CLARIFICATION_PENDING)
    db.commit()
    return selected
