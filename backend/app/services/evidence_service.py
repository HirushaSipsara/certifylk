import asyncio
import base64
import hashlib
import io
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai import AIProvider
from app.core.config import get_settings
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
    SelfAssessmentValue,
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
    execution: AIExecutionResult[EvidenceAnalysisOutput] | None
    review_status: str
    failed_evidence_request_ids: list[uuid.UUID]
    message: str | None = None

    @property
    def provider(self) -> str | None:
        return self.execution.provider if self.execution else None

    @property
    def fallback_used(self) -> bool | None:
        return self.execution.fallback_used if self.execution else None


MAX_AI_EVIDENCE_RAW_BYTES_PER_BATCH = 12 * 1024 * 1024
MAX_AI_EVIDENCE_FILES_PER_BATCH = 1
logger = logging.getLogger("certifylk.evidence")


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


def save_evidence_self_assessment(
    db: Session,
    assessment: Assessment,
    request: EvidenceRequest,
    value: str,
) -> EvidenceRequest:
    validate_page_transition(
        assessment,
        {AssessmentStatus.EVIDENCE_PENDING, AssessmentStatus.EVIDENCE_COMPLETE},
        "Evidence self-assessment",
    )
    request.self_assessment = SelfAssessmentValue(value)
    if assessment.status == AssessmentStatus.EVIDENCE_COMPLETE:
        update_assessment_progress(assessment, AssessmentStatus.EVIDENCE_PENDING)
    db.commit()
    return request


async def analyze_uploaded_evidence(
    db: Session,
    assessment: Assessment,
    storage: StorageProvider,
    provider: AIProvider | None = None,
    per_file_timeout_seconds: float | None = None,
    total_timeout_seconds: float | None = None,
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
    if assessment.scheme_id and any(request.self_assessment is None for request in requests):
        raise TransitionError("Answer the current-state question for every requirement.")
    if not assessment.scheme_id and any(
        request.status == EvidenceRequestStatus.REQUESTED and request.self_assessment is None
        for request in requests
    ):
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
        update_assessment_progress(assessment, AssessmentStatus.EVIDENCE_COMPLETE)
        db.commit()
        return PersistedEvidenceAnalysis(
            observations=[],
            execution=None,
            review_status="not_requested",
            failed_evidence_request_ids=[],
            message=(
                "No supporting files were submitted. Your self-assessment answers were saved "
                "and you can continue."
            ),
        )

    async def analyze_batch(
        batch: list[EvidenceInput],
        batch_number: int,
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

        batch_files = [file_by_request[item.request_id] for item in batch]
        diagnostic_context: dict[str, object] = {
            "batch_number": batch_number,
            "batch_count": len(batches),
            "batch_size": len(batch),
            "evidence_request_ids": [str(item.request_id) for item in batch],
            "evidence_file_ids": [str(item.id) for item in batch_files],
            "mime_types": [item.content_type for item in batch_files],
            "byte_sizes": [item.size_bytes for item in batch_files],
        }
        logger.info(
            "evidence_batch_start assessment_id=%s context=%s",
            assessment.id,
            diagnostic_context,
        )
        result = await run_with_validation(
            db,
            assessment.id,
            "analyze_evidence",
            call,
            lambda candidate: validate_evidence_output(candidate, batch_requirements),
            provider_override=provider,
            diagnostic_context=diagnostic_context,
            max_attempts=1,
            allow_fallback=False,
            timeout_seconds=batch_timeout_seconds,
        )
        logger.info(
            "evidence_batch_complete assessment_id=%s batch_number=%s provider=%s "
            "fallback_used=%s validation_status=%s observation_count=%s",
            assessment.id,
            batch_number,
            result.provider,
            result.fallback_used,
            result.validation_status,
            len(result.output.observations),
        )
        return result

    # Keep live multimodal calls sequential. This avoids self-inflicted provider quota
    # spikes while each independently validated batch preserves its own outcome.
    settings = get_settings()
    configured_per_file_timeout = (
        per_file_timeout_seconds
        if per_file_timeout_seconds is not None
        else settings.evidence_ai_timeout_seconds
    )
    configured_total_timeout = (
        total_timeout_seconds
        if total_timeout_seconds is not None
        else settings.evidence_ai_total_timeout_seconds
    )
    batch_timeout_seconds = configured_per_file_timeout
    loop = asyncio.get_running_loop()
    deadline = loop.time() + configured_total_timeout
    executions: list[AIExecutionResult[EvidenceAnalysisOutput]] = []
    failed_request_ids: list[uuid.UUID] = []
    for batch_number, batch in enumerate(batches, start=1):
        remaining = deadline - loop.time()
        if remaining <= 0:
            failed_request_ids.extend(item.request_id for item in batch)
            continue
        batch_timeout_seconds = min(configured_per_file_timeout, remaining)
        try:
            executions.append(await analyze_batch(batch, batch_number))
        except AppError as exc:
            failed_request_ids.extend(item.request_id for item in batch)
            logger.warning(
                "evidence_batch_unavailable assessment_id=%s batch_number=%s "
                "exception=%s message=%s",
                assessment.id,
                batch_number,
                type(exc).__name__,
                exc.message,
            )
    output = EvidenceAnalysisOutput(
        observations=[
            observation
            for batch_execution in executions
            for observation in batch_execution.output.observations
        ]
    )
    execution = (
        AIExecutionResult(
            output=output,
            provider=("mock" if any(item.provider == "mock" for item in executions) else "gemini"),
            fallback_used=any(item.fallback_used for item in executions),
            validation_status="validated",
        )
        if executions
        else None
    )
    execution_by_pair = {
        (observation.evidence_request_id, observation.requirement_id): batch_execution
        for batch_execution in executions
        for observation in batch_execution.output.observations
    }
    observations = merge_evidence_observations(
        db,
        assessment,
        output,
        file_by_request,
        execution_by_pair,
        successful_request_ids={
            observation.evidence_request_id for observation in output.observations
        },
    )
    successful_request_ids = {
        observation.evidence_request_id for observation in output.observations
    }
    for request in requests:
        if (
            request.status == EvidenceRequestStatus.UPLOADED
            and request.id in successful_request_ids
        ):
            request.status = EvidenceRequestStatus.ANALYZED
    update_assessment_progress(assessment, AssessmentStatus.EVIDENCE_COMPLETE)
    db.commit()
    if failed_request_ids and executions:
        review_status = "partial"
    elif failed_request_ids:
        review_status = "unavailable"
    else:
        review_status = "complete"
    message = (
        "AI evidence review is temporarily unavailable for one or more uploaded files. "
        "Your files and self-assessment answers are saved, and you may continue."
        if failed_request_ids
        else None
    )
    return PersistedEvidenceAnalysis(
        observations=observations,
        execution=execution,
        review_status=review_status,
        failed_evidence_request_ids=failed_request_ids,
        message=message,
    )


def merge_evidence_observations(
    db: Session,
    assessment: Assessment,
    output: EvidenceAnalysisOutput,
    file_by_request: dict[uuid.UUID, EvidenceFile],
    execution_by_pair: dict[tuple[uuid.UUID, str], AIExecutionResult[EvidenceAnalysisOutput]],
    successful_request_ids: set[uuid.UUID] | None = None,
) -> list[EvidenceObservation]:
    successful = successful_request_ids or {
        observation.evidence_request_id for observation in output.observations
    }
    if successful:
        db.execute(
            delete(EvidenceObservation).where(
                EvidenceObservation.assessment_id == assessment.id,
                EvidenceObservation.evidence_request_id.in_(successful),
            )
        )
    observations: list[EvidenceObservation] = []
    now = datetime.now(timezone.utc)
    for item in output.observations:
        evidence_file = file_by_request.get(item.evidence_request_id)
        item_execution = execution_by_pair[(item.evidence_request_id, item.requirement_id)]
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
            provider=item_execution.provider,
            fallback_used=item_execution.fallback_used,
            validation_status=item_execution.validation_status,
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
