"""Tests for evidence storage safety, postgres decimal precision, and status re-entrancy."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Assessment, EvidenceObservation, EvidenceRequest
from app.models.enums import (
    AssessmentPage,
    AssessmentStatus,
    EvidenceKind,
    EvidenceRequestStatus,
    ObservationPolarity,
)
from app.schemas.ai import EvidenceAnalysisOutput, EvidenceObservationOutput
from app.services.evidence_service import (
    analyze_uploaded_evidence,
    merge_evidence_observations,
)
from app.storage.local import LocalStorageProvider


def test_local_storage_provider_missing_file(tmp_path):
    """LocalStorageProvider.open_file should raise structured AppError(404) when file is missing."""
    provider = LocalStorageProvider(tmp_path)
    key = "non_existent/file.png"
    with pytest.raises(AppError) as exc_info:
        provider.open_file(key)
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "file_not_found"


def test_merge_evidence_observations_decimal_precision(db: Session):
    """merge_evidence_observations must format confidence with 4 decimal places for Numeric(5, 4)."""
    assessment = Assessment(
        status=AssessmentStatus.EVIDENCE_PENDING,
        current_page=AssessmentPage.EVIDENCE,
    )
    db.add(assessment)
    db.commit()

    request = EvidenceRequest(
        assessment_id=assessment.id,
        evidence_type="production_area",
        kind=EvidenceKind.PHOTO,
        title="Production Area Photo",
        requirement_ids=["REQ_1"],
        required=True,
        status=EvidenceRequestStatus.UPLOADED,
        display_order=1,
    )
    db.add(request)
    db.commit()

    output = EvidenceAnalysisOutput(
        observations=[
            EvidenceObservationOutput(
                evidence_request_id=request.id,
                requirement_id="REQ_1",
                polarity="supports",
                text="Photo shows clean equipment.",
                confidence=0.8200000000000001,  # Raw float from JSON / AI
            )
        ]
    )

    observations = merge_evidence_observations(db, assessment, output, {})
    assert len(observations) == 1
    obs = observations[0]
    assert obs.confidence == Decimal("0.8200")
    assert obs.polarity == ObservationPolarity.SUPPORTS


@pytest.mark.asyncio
async def test_analyze_uploaded_evidence_reentrant(db: Session, tmp_path):
    """Completed evidence analysis should return existing observations without re-running AI."""
    provider = LocalStorageProvider(tmp_path)
    assessment = Assessment(
        status=AssessmentStatus.EVIDENCE_COMPLETE,
        current_page=AssessmentPage.EVIDENCE,
    )
    db.add(assessment)
    db.commit()

    request = EvidenceRequest(
        assessment_id=assessment.id,
        evidence_type="production_area",
        kind=EvidenceKind.PHOTO,
        title="Production Area Photo",
        requirement_ids=["REQ_1"],
        required=True,
        status=EvidenceRequestStatus.ANALYZED,
        display_order=1,
    )
    db.add(request)
    db.commit()

    obs = EvidenceObservation(
        assessment_id=assessment.id,
        evidence_request_id=request.id,
        requirement_id="REQ_1",
        polarity=ObservationPolarity.SUPPORTS,
        text="Clean production area.",
        confidence=Decimal("0.8500"),
        provider="validated_ai",
    )
    db.add(obs)
    db.commit()

    analysis = await analyze_uploaded_evidence(db, assessment, provider)
    assert len(analysis.observations) == 1
    assert analysis.observations[0].text == "Clean production area."
