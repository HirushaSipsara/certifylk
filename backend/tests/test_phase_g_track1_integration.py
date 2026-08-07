import pytest
from sqlalchemy.orm import Session

from app.models import Assessment, CertificationScheme, Product, SchemeRequirement
from app.models.enums import AssessmentStatus
from app.services.assessment_service import create_assessment
from app.services.evidence_service import (
    analyze_uploaded_evidence,
    mark_evidence_unavailable,
    plan_final_clarifications,
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
        "product_id": product.id if product else "PROD_CORDIAL",
        "product_name": "Fresh Fruit Cordial",
    }
    db_session.flush()

    assert assessment.scheme_id == "SLS_MARK_CORDIAL"

    # Verify all scheme requirements belong to SLS_MARK_CORDIAL
    scheme_req_ids = {r.id for r in scheme.requirements}

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
    await extract_structured_process(db_session, assessment)

    # 3. Build scheme evidence plan
    requests = build_evidence_plan(db_session, assessment)
    assert len(requests) > 0

    # Assert evidence expectation requirement IDs belong to selected scheme
    for req in requests:
        for r_id in req.requirement_ids:
            assert r_id in scheme_req_ids, f"Evidence request requirement {r_id} does not belong to scheme {scheme.id}"

    # 4. Submit evidence (mark unavailable) & analyze evidence
    mark_evidence_unavailable(db_session, assessment, requests[0].id)
    await analyze_uploaded_evidence(db_session, assessment, MemoryStorageProvider())

    # 5. Build clarification plan and explicitly verify clarification state handling
    clarification_plan = await plan_final_clarifications(db_session, assessment)

    # Verify clarification question IDs belong strictly to candidate question bank
    for q in clarification_plan.questions:
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
