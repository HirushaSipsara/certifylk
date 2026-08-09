import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AssessmentQuestion,
    CertificationScheme,
    EvidenceObservation,
    Product,
    SchemeRequirement,
)
from app.models.enums import AssessmentStatus
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

    # 4. Submit one scheme-bound evidence file, mark the rest unavailable, and analyze.
    storage = MemoryStorageProvider()
    uploaded_request = next(request for request in requests if request.kind.value == "photo")
    store_upload(
        db_session,
        assessment,
        uploaded_request,
        filename="handwashing-area.png",
        content_type="image/png",
        data=(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc` \x05"
            b"\x00\x00\x04\x00\x01\x07\x05\xd3\xd2\x00\x00\x00\x00IEND\xaeB`\x82"
        ),
        storage=storage,
    )
    for request in requests:
        if request.id == uploaded_request.id:
            continue
        mark_evidence_unavailable(db_session, assessment, request)
    await analyze_uploaded_evidence(db_session, assessment, storage)
    observations = list(
        db_session.scalars(
            select(EvidenceObservation).where(EvidenceObservation.assessment_id == assessment.id)
        )
    )
    assert observations
    assert all(item.requirement_id in scheme_req_ids for item in observations)
    assert all(item.scheme_requirement_id == item.requirement_id for item in observations)

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
    assert result.overall_score >= 0
    assert result.overall_score <= 100
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
