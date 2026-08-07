import pytest
from sqlalchemy.orm import Session

from app.models import Assessment, BusinessProfile, Product
from app.models.enums import AssessmentStatus
from app.services.ai_service import MockAIProvider
from app.services.applicability_service import run_applicability_agent
from app.services.assessment_service import create_assessment
from app.services.process_service import build_evidence_plan
from app.services.result_service import generate_scheme_result, serialize_result
from app.services.seed_service import seed_initial_knowledge_base


@pytest.mark.asyncio
async def test_track2_domestic_vs_export_applicability(db_session: Session):
    """Verify Track 2 domestic vs export applicability recommendations and scheme isolation."""
    seed_initial_knowledge_base(db_session)
    provider = MockAIProvider()

    # Case A: Domestic Supermarket Case
    profile_domestic = BusinessProfile(
        id="bp_domestic",
        name="Domestic Foods",
        business_type="Sole Proprietorship",
        scale="Micro",
        market=["Domestic Supermarkets"],
        existing_certifications=[],
        has_food_licence="yes",
    )
    db_session.add(profile_domestic)

    assessment_dom = create_assessment(db_session)
    assessment_dom.profile_id = profile_domestic.id
    db_session.flush()

    res_dom = await run_applicability_agent(db_session, assessment_dom.id, provider=provider)
    assert res_dom.recommended_path_scheme_id in {"SLS_GMP", "SLS_HACCP"}

    # Case B: Export Case
    profile_export = BusinessProfile(
        id="bp_export",
        name="Lanka Export Foods Ltd",
        business_type="Formal Enterprise",
        scale="Medium",
        market=["Export"],
        existing_certifications=["SLS_GMP", "SLS_HACCP"],
        has_food_licence="yes",
    )
    db_session.add(profile_export)

    assessment_exp = create_assessment(db_session)
    assessment_exp.profile_id = profile_export.id
    db_session.flush()

    res_exp = await run_applicability_agent(db_session, assessment_exp.id, provider=provider)
    assert res_exp.recommended_path_scheme_id == "ISO_22000"


@pytest.mark.asyncio
async def test_track2_gmp_vs_iso22000_isolation(db_session: Session):
    """Verify that GMP requirements and evidence expectations do not leak into ISO 22000 assessment."""
    seed_initial_knowledge_base(db_session)

    # Assessment bound to ISO_22000
    assessment_iso = create_assessment(db_session)
    assessment_iso.scheme_id = "ISO_22000"
    assessment_iso.profile_data = {"name": "Export Factory", "scale": "Medium"}
    db_session.flush()

    requests = build_evidence_plan(db_session, assessment_iso)
    assert len(requests) > 0

    # Ensure all evidence requests belong to ISO_22000 requirements
    from app.models import SchemeRequirement
    iso_req_ids = set(
        db_session.scalars(
            select_scheme_req_ids("ISO_22000")
        )
    )
    for req in requests:
        for r_id in req.requirement_ids:
            assert r_id in iso_req_ids, f"Requirement {r_id} does not belong to ISO_22000"


def select_scheme_req_ids(scheme_id: str):
    from sqlalchemy import select
    return select(SchemeRequirement.id).where(SchemeRequirement.scheme_id == scheme_id)
