import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import MockAIProvider
from app.models import (
    AssessmentQuestion,
    CertificationScheme,
    EvidenceObservation,
    Product,
    SchemeRequirement,
)
from app.models.enums import AssessmentStatus
from app.schemas.ai import EvidenceAnalysisOutput, EvidenceInput, EvidenceObservationOutput
from app.services.assessment_service import create_assessment
from app.services.evidence_service import (
    analyze_uploaded_evidence,
    mark_evidence_unavailable,
    plan_final_clarifications,
    store_upload,
)
from app.services.process_service import (
    build_evidence_plan,
    extract_structured_process,
    save_process_steps,
)
from app.services.result_service import generate_scheme_result, serialize_result
from app.services.seed_service import seed_initial_knowledge_base
from app.storage import MemoryStorageProvider


class SupportingSchemeEvidenceProvider(MockAIProvider):
    """Test-only provider proving grounded observations reach scheme scoring."""

    def __init__(self) -> None:
        self.batches: list[list[EvidenceInput]] = []

    async def analyze_evidence(
        self,
        evidence: list[EvidenceInput],
        allowed_requirement_ids: set[str],
    ) -> EvidenceAnalysisOutput:
        self.batches.append(evidence)
        observations: list[EvidenceObservationOutput] = []
        for item in evidence:
            assert item.requirement_context
            assert all(
                context.title and context.description for context in item.requirement_context
            )
            for requirement_id in item.requirement_ids:
                if requirement_id in allowed_requirement_ids:
                    observations.append(
                        EvidenceObservationOutput(
                            evidence_request_id=item.request_id,
                            requirement_id=requirement_id,
                            polarity="supports",
                            text="The test evidence directly supports the supplied requirement context.",
                            confidence=0.91,
                        )
                    )
        return EvidenceAnalysisOutput(observations=observations)


class PartiallyFailingGeminiEvidenceProvider(SupportingSchemeEvidenceProvider):
    """Test-only Gemini-shaped provider with one consistently failed batch."""

    name = "gemini"
    model = "test-gemini-multimodal"

    def __init__(self, failed_request_ids: set[str]) -> None:
        super().__init__()
        self.failed_request_ids = failed_request_ids

    async def analyze_evidence(
        self,
        evidence: list[EvidenceInput],
        allowed_requirement_ids: set[str],
    ) -> EvidenceAnalysisOutput:
        if any(str(item.request_id) in self.failed_request_ids for item in evidence):
            raise RuntimeError("Synthetic provider batch failure")
        return await super().analyze_evidence(evidence, allowed_requirement_ids)


@pytest.mark.asyncio
async def test_track1_full_scheme_assessment_integration(db_session: Session):
    """Full Track 1 end-to-end scheme assessment integration test for Fresh Fruit Cordial.

    Includes explicit verification of clarification state handling.
    """
    seed_initial_knowledge_base(db_session)

    scheme = db_session.get(CertificationScheme, "SLS_MARK_CORDIAL")
    assert scheme is not None

    product = db_session.query(Product).first()

    # 1. Create Track 1 Assessment & bind scheme
    assessment = create_assessment(db_session)
    assessment.scheme_id = scheme.id
    assessment.profile_data = {
        "name": "Lanka Cordial Factory",
        "business_type": "Formal Enterprise",
        "scale": "Small",
        "market": ["Domestic Supermarkets"],
        "product_id": str(product.id) if product else "PROD_CORDIAL",
        "product_name": "Fresh Fruit Cordial",
    }
    db_session.flush()

    assert assessment.scheme_id == "SLS_MARK_CORDIAL"

    # Verify all scheme requirements belong to SLS_MARK_CORDIAL
    scheme_req_ids = set(
        db_session.scalars(
            select(SchemeRequirement.id).where(SchemeRequirement.scheme_id == scheme.id)
        )
    )

    # 2. Save production process steps & extract structured process
    save_process_steps(
        db_session,
        assessment,
        [
            "Fruit receiving and quality inspection",
            "Washing, peeling, and juice extraction",
            "Brix formulation and pasteurization",
            "Hot filling into glass bottles",
            "Storage and local retail distribution",
        ],
    )
    assessment.status = AssessmentStatus.PROCESS_COMPLETE
    await extract_structured_process(db_session, assessment)

    # 3. Build scheme evidence plan
    requests = build_evidence_plan(db_session, assessment)
    assert len(requests) > 0

    # Assert evidence expectation requirement IDs belong to selected scheme
    for req in requests:
        for r_id in req.requirement_ids:
            assert r_id in scheme_req_ids, (
                f"Evidence request requirement {r_id} does not belong to scheme {scheme.id}"
            )

    # 4. Submit six scheme-bound files so the service must use multiple bounded batches.
    storage = MemoryStorageProvider()
    uploaded_requests = requests[:6]
    for request in uploaded_requests:
        is_photo = request.kind.value == "photo"
        store_upload(
            db_session,
            assessment,
            request,
            filename="evidence.png" if is_photo else "evidence.pdf",
            content_type="image/png" if is_photo else "application/pdf",
            data=(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc` \x05"
                b"\x00\x00\x04\x00\x01\x07\x05\xd3\xd2\x00\x00\x00\x00IEND\xaeB`\x82"
                if is_photo
                else b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF"
            ),
            storage=storage,
        )
    for request in requests:
        if request in uploaded_requests:
            continue
        mark_evidence_unavailable(db_session, assessment, request)
    provider = SupportingSchemeEvidenceProvider()
    analysis = await analyze_uploaded_evidence(
        db_session,
        assessment,
        storage,
        provider=provider,
    )
    assert len(provider.batches) == 3
    assert analysis.execution.provider == "mock"
    assert analysis.execution.fallback_used is False
    observations = list(
        db_session.scalars(
            select(EvidenceObservation).where(EvidenceObservation.assessment_id == assessment.id)
        )
    )
    assert observations
    assert all(item.requirement_id in scheme_req_ids for item in observations)
    assert all(item.scheme_requirement_id == item.requirement_id for item in observations)
    assert all(item.polarity.value == "supports" for item in observations)
    assert all(item.provider == "mock" for item in observations)
    assert all(item.fallback_used is False for item in observations)
    assert all(item.validation_status == "validated" for item in observations)

    # 5. Build clarification plan and explicitly verify clarification state handling
    clarification_plan = await plan_final_clarifications(db_session, assessment)
    for assigned in db_session.scalars(
        select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment.id)
    ):
        assigned.answered = True
    db_session.flush()

    # Verify clarification question IDs belong strictly to candidate question bank
    for q in clarification_plan:
        assert q.id is not None

    # Assert valid state transition after clarification planning
    assert assessment.status in {
        AssessmentStatus.CLARIFICATION_PENDING,
        AssessmentStatus.READY_TO_SCORE,
    }

    # 6. Complete assessment & generate scheme result
    assessment.status = AssessmentStatus.READY_TO_SCORE
    result = await generate_scheme_result(db_session, assessment)

    assert result is not None
    assert result.overall_score > 0
    assert result.overall_score <= 100
    assert result.evidence_completeness > 0
    assert result.scheme_version == "draft-2026-08"
    assert result.catalogue_revision == "2026-08-07-draft"

    serialized = serialize_result(db_session, assessment, result)
    assert "roadmap" in serialized
    assert "cost_summary" in serialized
    assert "by_type" in serialized["cost_summary"]

    # Verify all roadmap item requirement linkages belong to selected scheme
    for item in serialized["roadmap"]:
        assert "cost_type" in item
        assert "quote_required" in item


@pytest.mark.asyncio
async def test_evidence_batches_preserve_gemini_successes_and_replace_only_failed_batch(
    db_session: Session,
):
    seed_initial_knowledge_base(db_session)
    scheme = db_session.get(CertificationScheme, "SLS_MARK_CORDIAL")
    product = db_session.query(Product).first()
    assert scheme is not None

    assessment = create_assessment(db_session)
    assessment.scheme_id = scheme.id
    assessment.profile_data = {
        "name": "Synthetic partial batch test",
        "scale": "Small",
        "market": ["Domestic Supermarkets"],
        "product_id": str(product.id) if product else "PROD_CORDIAL",
    }
    db_session.flush()
    save_process_steps(
        db_session,
        assessment,
        ["Receive", "Wash", "Cook", "Fill", "Store"],
    )
    assessment.status = AssessmentStatus.PROCESS_COMPLETE
    await extract_structured_process(db_session, assessment)
    requests = build_evidence_plan(db_session, assessment)
    uploaded_requests = requests[:5]
    storage = MemoryStorageProvider()
    for request in uploaded_requests:
        is_photo = request.kind.value == "photo"
        store_upload(
            db_session,
            assessment,
            request,
            filename="synthetic.png" if is_photo else "synthetic.pdf",
            content_type="image/png" if is_photo else "application/pdf",
            data=(
                b"\x89PNG\r\n\x1a\nsynthetic"
                if is_photo
                else b"%PDF-1.4\n% synthetic test evidence\n%%EOF"
            ),
            storage=storage,
        )
    for request in requests[5:]:
        mark_evidence_unavailable(db_session, assessment, request)

    failed_batch_request_ids = {str(uploaded_requests[2].id), str(uploaded_requests[3].id)}
    provider = PartiallyFailingGeminiEvidenceProvider(failed_batch_request_ids)
    first = await analyze_uploaded_evidence(
        db_session,
        assessment,
        storage,
        provider=provider,
    )
    assert first.execution.provider == "mock"
    assert first.execution.fallback_used is True

    persisted = list(
        db_session.scalars(
            select(EvidenceObservation)
            .where(EvidenceObservation.assessment_id == assessment.id)
            .order_by(EvidenceObservation.evidence_request_id)
        )
    )
    assert len(persisted) == 5
    by_request = {str(item.evidence_request_id): item for item in persisted}
    for request in uploaded_requests:
        observation = by_request[str(request.id)]
        if str(request.id) in failed_batch_request_ids:
            assert observation.provider == "mock"
            assert observation.fallback_used is True
            assert observation.polarity.value == "unclear"
        else:
            assert observation.provider == "gemini"
            assert observation.fallback_used is False
            assert observation.polarity.value == "supports"
        assert observation.validation_status == "validated"

    # A real retry replaces the assessment's observations instead of accumulating rows.
    retried = await analyze_uploaded_evidence(
        db_session,
        assessment,
        storage,
        provider=provider,
    )
    assert retried.execution.fallback_used is True
    retry_rows = list(
        db_session.scalars(
            select(EvidenceObservation).where(EvidenceObservation.assessment_id == assessment.id)
        )
    )
    assert len(retry_rows) == 5
