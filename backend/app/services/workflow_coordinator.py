"""Typed Workflow Coordinator for CertifyLK assessments.

Sequences allowed assessment operations, enforces status transitions, and guarantees
scheme isolation. Reuses existing domain services.
"""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import Assessment, EvidenceFile, EvidenceRequest
from app.models.enums import CertificationTrack
from app.schemas.ai import ApplicabilityDecisionOutput
from app.schemas.assessment import ClarificationInput, ProcessInput, ProfileInput
from app.services.applicability_service import run_applicability_agent
from app.services.assessment_service import create_assessment, get_assessment
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
from app.services.profile_service import save_profile_answers
from app.services.result_service import generate_result, generate_scheme_result
from app.storage import StorageProvider


class AssessmentWorkflowCoordinator:
    """Typed application service for coordinating assessment lifecycle."""

    @staticmethod
    def create_assessment(db: Session) -> Assessment:
        return create_assessment(db)

    @staticmethod
    def get_assessment(db: Session, assessment_id: uuid.UUID) -> Assessment:
        return get_assessment(db, assessment_id)

    @staticmethod
    def update_profile(db: Session, assessment_id: uuid.UUID, data: dict[str, Any]) -> Assessment:
        assessment = get_assessment(db, assessment_id)
        return save_profile_answers(db, assessment, ProfileInput.model_validate(data))

    @staticmethod
    async def run_applicability(
        db: Session, assessment_id: uuid.UUID, track: CertificationTrack | None = None
    ) -> ApplicabilityDecisionOutput:
        assessment = get_assessment(db, assessment_id)
        return await run_applicability_agent(db, assessment, track=track)

    @staticmethod
    def save_process(db: Session, assessment_id: uuid.UUID, payload: ProcessInput) -> Assessment:
        assessment = get_assessment(db, assessment_id)
        return save_adaptive_answers(db, assessment, payload)

    @staticmethod
    async def analyze_process(db: Session, assessment_id: uuid.UUID) -> Any:
        assessment = get_assessment(db, assessment_id)
        return await extract_structured_process(db, assessment)

    @staticmethod
    def build_evidence_plan(db: Session, assessment_id: uuid.UUID) -> list[EvidenceRequest]:
        assessment = get_assessment(db, assessment_id)
        return build_evidence_plan(db, assessment)

    @staticmethod
    def upload_evidence(
        db: Session,
        assessment_id: uuid.UUID,
        evidence_request_id: uuid.UUID,
        *,
        filename: str,
        content_type: str,
        data: bytes,
        storage: StorageProvider,
    ) -> EvidenceFile:
        assessment = get_assessment(db, assessment_id)
        request = get_evidence_request(db, assessment.id, evidence_request_id)
        return store_upload(
            db,
            assessment,
            request,
            filename=filename,
            content_type=content_type,
            data=data,
            storage=storage,
        )

    @staticmethod
    def mark_evidence_unavailable(
        db: Session, assessment_id: uuid.UUID, evidence_request_id: uuid.UUID
    ) -> EvidenceRequest:
        assessment = get_assessment(db, assessment_id)
        request = get_evidence_request(db, assessment.id, evidence_request_id)
        return mark_evidence_unavailable(db, assessment, request)

    @staticmethod
    async def analyze_evidence(
        db: Session, assessment_id: uuid.UUID, storage: StorageProvider
    ) -> Any:
        assessment = get_assessment(db, assessment_id)
        return await analyze_uploaded_evidence(db, assessment, storage)

    @staticmethod
    async def plan_clarifications(db: Session, assessment_id: uuid.UUID) -> Any:
        assessment = get_assessment(db, assessment_id)
        return await plan_final_clarifications(db, assessment)

    @staticmethod
    def submit_clarifications(
        db: Session, assessment_id: uuid.UUID, payload: ClarificationInput
    ) -> Assessment:
        assessment = get_assessment(db, assessment_id)
        return save_clarification_answers(db, assessment, payload)

    @staticmethod
    async def complete_assessment(db: Session, assessment_id: uuid.UUID) -> Any:
        assessment = get_assessment(db, assessment_id)
        if assessment.scheme_id:
            return await generate_scheme_result(db, assessment)
        return await generate_result(db, assessment)
