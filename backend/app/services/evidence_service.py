import asyncio
import base64
import hashlib
import io
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai import AIProvider
from app.core.errors import AppError, NotFoundError, TransitionError
from app.models import (
    Assessment,
    AssessmentQuestion,
    EvidenceFile,
    EvidenceObservation,
    EvidenceRequest,
    QuestionBank,
    Requirement,
)
from app.models.enums import (
    AssessmentStatus,
    EvidenceRequestStatus,
    ObservationPolarity,
    QuestionPage,
)
from app.schemas.ai import (
    EvidenceAnalysisOutput,
    EvidenceInput,
    EvidenceRequirementContext,
    QuestionPlanOutput,
)
from app.services.ai_service import (
    AIExecutionResult,
    run_with_validation,
    validate_evidence_output,
    validate_question_plan,
    wrap_untrusted_evidence_data,
)
from app.services.assessment_service import update_assessment_progress, validate_page_transition
from app.services.storage_service import (
    delete_file,
    generate_safe_storage_key,
    sanitize_original_filename,
    validate_upload,
)
from app.storage import StorageProvider


@dataclass(frozen=True)
class PersistedEvidenceAnalysis:
    observations: list[EvidenceObservation]
    execution: AIExecutionResult[EvidenceAnalysisOutput]


MAX_AI_EVIDENCE_FILES_PER_BATCH = 5
MAX_AI_EVIDENCE_RAW_BYTES_PER_BATCH = 12 * 1024 * 1024
MAX_CONCURRENT_EVIDENCE_BATCHES = 3


def _partition_evidence_inputs(
    inputs: list[EvidenceInput],
    raw_sizes: dict[uuid.UUID, int],
) -> list[list[EvidenceInput]]:
    """Bound multimodal requests by file count and approximate raw payload size."""
    batches: list[list[EvidenceInput]] = []
    current: list[EvidenceInput] = []
    current_size = 0
    for item in inputs:
        item_size = raw_sizes.get(item.request_id, 0)
        if current and (
            len(current) >= MAX_AI_EVIDENCE_FILES_PER_BATCH
            or current_size + item_size > MAX_AI_EVIDENCE_RAW_BYTES_PER_BATCH
        ):
            batches.append(current)
            current = []
            current_size = 0
        current.append(item)
        current_size += item_size
    if current:
        batches.append(current)
    return batches


def _requirement_context_by_id(
    db: Session,
    assessment: Assessment,
) -> dict[str, EvidenceRequirementContext]:
    if assessment.scheme_id:
        from app.services.catalog_service import get_scheme_requirements

        requirements = get_scheme_requirements(db, assessment.scheme_id)
    else:
        requirements = list(db.scalars(select(Requirement).where(Requirement.active.is_(True))))
    return {
        requirement.id: EvidenceRequirementContext(
            requirement_id=requirement.id,
            title=requirement.title,
            description=requirement.description,
            source_document=str(getattr(requirement, "source_document", "")),
            clause_reference=str(getattr(requirement, "clause_reference", "")),
            content_verified=getattr(requirement, "content_verified", None),
            evaluation_rule=dict(requirement.evaluation_rule or {}),
        )
        for requirement in requirements
    }


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


def reset_evidence_request(
    db: Session,
    assessment: Assessment,
    request: EvidenceRequest,
    storage: StorageProvider,
) -> EvidenceRequest:
    """Remove stored file (if any), delete DB record, and reset request to REQUESTED."""
    validate_page_transition(
        assessment,
        {AssessmentStatus.EVIDENCE_PENDING, AssessmentStatus.EVIDENCE_COMPLETE},
        "Evidence reset",
    )
    if request.status not in (
        EvidenceRequestStatus.UPLOADED,
        EvidenceRequestStatus.UNAVAILABLE,
        EvidenceRequestStatus.ANALYZED,
    ):
        raise TransitionError("Only uploaded or unavailable evidence items can be reset.")
    existing_files = list(
        db.scalars(select(EvidenceFile).where(EvidenceFile.evidence_request_id == request.id))
    )
    for evidence_file in existing_files:
        try:
            delete_file(storage, evidence_file.storage_key)
        except Exception:
            pass  # Non-fatal: file may already be missing
        db.delete(evidence_file)
    db.execute(
        delete(EvidenceObservation).where(
            EvidenceObservation.assessment_id == assessment.id,
            EvidenceObservation.evidence_request_id == request.id,
        )
    )
    request.status = EvidenceRequestStatus.REQUESTED
    update_assessment_progress(assessment, AssessmentStatus.EVIDENCE_PENDING)
    db.commit()
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
    # If item was previously resolved (uploaded/unavailable), auto-reset before accepting new upload
    if request.status in (
        EvidenceRequestStatus.UPLOADED,
        EvidenceRequestStatus.UNAVAILABLE,
    ):
        existing_files = list(
            db.scalars(select(EvidenceFile).where(EvidenceFile.evidence_request_id == request.id))
        )
        for evidence_file in existing_files:
            try:
                delete_file(storage, evidence_file.storage_key)
            except Exception:
                pass
            db.delete(evidence_file)
        db.flush()
        request.status = EvidenceRequestStatus.REQUESTED
    if request.status != EvidenceRequestStatus.REQUESTED:
        raise TransitionError("This evidence request cannot be updated at this stage.")
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
    db: Session,
    assessment: Assessment,
    request: EvidenceRequest,
    storage: StorageProvider | None = None,
) -> EvidenceRequest:
    validate_page_transition(
        assessment, {AssessmentStatus.EVIDENCE_PENDING}, "Mark evidence unavailable"
    )
    # If previously uploaded, remove the stored file before marking unavailable
    if request.status == EvidenceRequestStatus.UPLOADED:
        existing_files = list(
            db.scalars(select(EvidenceFile).where(EvidenceFile.evidence_request_id == request.id))
        )
        for evidence_file in existing_files:
            if storage:
                try:
                    delete_file(storage, evidence_file.storage_key)
                except Exception:
                    pass
            db.delete(evidence_file)
        db.flush()
    elif request.status != EvidenceRequestStatus.REQUESTED:
        raise TransitionError("This evidence request cannot be updated at this stage.")
    request.status = EvidenceRequestStatus.UNAVAILABLE
    db.commit()
    return request


async def analyze_uploaded_evidence(
    db: Session,
    assessment: Assessment,
    storage: StorageProvider,
    provider: AIProvider | None = None,
) -> PersistedEvidenceAnalysis:
    validate_page_transition(
        assessment,
        {AssessmentStatus.EVIDENCE_PENDING, AssessmentStatus.EVIDENCE_COMPLETE},
        "Evidence analysis",
    )
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
    raw_sizes = {item.evidence_request_id: item.size_bytes for item in files}
    contexts = _requirement_context_by_id(db, assessment)
    evidence_inputs: list[EvidenceInput] = []
    for request in requests:
        evidence_file = file_by_request.get(request.id)
        if evidence_file is None:
            continue
        try:
            with storage.open_file(evidence_file.storage_key) as source:
                data = source.read()
        except FileNotFoundError as exc:
            raise AppError(
                "evidence_file_missing",
                f"Uploaded evidence file for '{request.title}' was not found in storage. Please re-upload the file.",
                400,
            ) from exc
        evidence_inputs.append(
            EvidenceInput(
                request_id=request.id,
                evidence_type=request.evidence_type,
                requirement_ids=request.requirement_ids,
                requirement_context=[
                    contexts[requirement_id]
                    for requirement_id in request.requirement_ids
                    if requirement_id in contexts
                ],
                content_type=evidence_file.content_type,
                safe_data_summary=wrap_untrusted_evidence_data(
                    f"Stored {request.title}; original content is attached as binary evidence."
                ),
                data_base64=base64.b64encode(data).decode("ascii"),
            )
        )
    request_requirements = {item.request_id: set(item.requirement_ids) for item in evidence_inputs}
    if assessment.scheme_id:
        from app.services.catalog_service import get_scheme_requirements

        scheme_reqs = get_scheme_requirements(db, assessment.scheme_id)
        scheme_req_ids = {r.id for r in scheme_reqs}
        allowed_requirements = {
            req_id
            for req_ids in request_requirements.values()
            for req_id in req_ids
            if req_id in scheme_req_ids
        }
    else:
        allowed_requirements = {
            requirement_id
            for requirement_ids in request_requirements.values()
            for requirement_id in requirement_ids
        }

    batches = _partition_evidence_inputs(evidence_inputs, raw_sizes)
    if not batches:
        batches = [[]]
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_EVIDENCE_BATCHES)

    async def analyze_batch(
        batch: list[EvidenceInput],
    ) -> AIExecutionResult[EvidenceAnalysisOutput]:
        batch_requirements = {
            item.request_id: set(item.requirement_ids) & allowed_requirements for item in batch
        }
        batch_allowed = {
            requirement_id
            for requirement_ids in batch_requirements.values()
            for requirement_id in requirement_ids
        }

        async def call(selected_provider: AIProvider) -> EvidenceAnalysisOutput:
            return await selected_provider.analyze_evidence(batch, batch_allowed)

        async with semaphore:
            return await run_with_validation(
                db,
                assessment.id,
                "analyze_evidence",
                call,
                lambda result: validate_evidence_output(result, batch_requirements),
                provider_override=provider,
            )

    executions = await asyncio.gather(*(analyze_batch(batch) for batch in batches))
    output = EvidenceAnalysisOutput(
        observations=[
            observation
            for batch_execution in executions
            for observation in batch_execution.output.observations
        ]
    )
    execution = AIExecutionResult(
        output=output,
        provider=("mock" if any(item.provider == "mock" for item in executions) else "gemini"),
        fallback_used=any(item.fallback_used for item in executions),
    )
    observations = merge_evidence_observations(db, assessment, output, file_by_request)
    for request in requests:
        if request.status == EvidenceRequestStatus.UPLOADED:
            request.status = EvidenceRequestStatus.ANALYZED
    update_assessment_progress(assessment, AssessmentStatus.EVIDENCE_COMPLETE)
    db.commit()
    return PersistedEvidenceAnalysis(observations=observations, execution=execution)


def merge_evidence_observations(
    db: Session,
    assessment: Assessment,
    output: EvidenceAnalysisOutput,
    file_by_request: dict[uuid.UUID, EvidenceFile],
) -> list[EvidenceObservation]:
    db.execute(
        delete(EvidenceObservation).where(EvidenceObservation.assessment_id == assessment.id)
    )
    observations: list[EvidenceObservation] = []
    now = datetime.now(timezone.utc)
    for item in output.observations:
        evidence_file = file_by_request.get(item.evidence_request_id)
        observation = EvidenceObservation(
            assessment_id=assessment.id,
            evidence_request_id=item.evidence_request_id,
            evidence_file_id=evidence_file.id if evidence_file else None,
            requirement_id=item.requirement_id,
            scheme_id=assessment.scheme_id,
            scheme_requirement_id=item.requirement_id if assessment.scheme_id else None,
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
    if assessment.scheme_id:
        from app.services.catalog_service import get_scheme_requirements

        scheme_reqs = get_scheme_requirements(db, assessment.scheme_id)
        scheme_req_ids = {r.id for r in scheme_reqs}
        supported_req_ids = set(
            db.scalars(
                select(EvidenceObservation.requirement_id).where(
                    EvidenceObservation.assessment_id == assessment.id,
                    EvidenceObservation.polarity == ObservationPolarity.SUPPORTS,
                )
            )
        )
        unresolved_req_ids = scheme_req_ids - supported_req_ids
        all_questions = list(
            db.scalars(
                select(QuestionBank)
                .where(QuestionBank.active.is_(True))
                .order_by(QuestionBank.priority.desc(), QuestionBank.id)
            )
        )
        return [
            q
            for q in all_questions
            if q.id not in assigned_ids
            and any(req_id in unresolved_req_ids for req_id in q.requirement_ids)
        ]
    else:
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
    if not candidates:
        update_assessment_progress(assessment, AssessmentStatus.READY_TO_SCORE)
        db.commit()
        return []

    candidate_ids = [question.id for question in candidates]
    context = {
        "profile": assessment.profile_data,
        "process_uncertainties": assessment.process_analysis.get("uncertainties", []),
    }
    min_count = min(1, len(candidate_ids))
    max_count = min(5, len(candidate_ids))

    async def call(provider: AIProvider) -> QuestionPlanOutput:
        return await provider.plan_clarifications(context, candidate_ids)

    execution = await run_with_validation(
        db,
        assessment.id,
        "plan_clarifications",
        call,
        lambda result: validate_question_plan(result, candidate_ids, min_count, max_count),
    )
    output = execution.output
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
