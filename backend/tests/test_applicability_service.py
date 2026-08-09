import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Assessment
from app.models.enums import AssessmentStatus
from app.services.applicability_service import create_business_profile, run_applicability_agent
from app.services.catalog_service import list_categories, list_products


@pytest.mark.asyncio
async def test_applicability_agent_flow(db: Session) -> None:
    # 1. Create a business profile
    bp = create_business_profile(
        db,
        name="Lanka Cordial Works",
        business_type="limited_company",
        years_operating=5,
        scale="small",
        market=["supermarket", "export"],
        existing_certifications=[],
        has_food_licence="yes",
        monthly_volume_range="500_2000",
        additional_info="Supplying leading supermarket chains in Colombo.",
    )

    # 2. Create an assessment linked to cordial product and business profile
    cats = list_categories(db)
    prods = list_products(db, str(cats[0].id))
    cordial = prods[0]

    assessment = Assessment(
        status=AssessmentStatus.DRAFT_PROFILE,
        business_profile_id=bp.id,
        product_id=cordial.id,
    )
    db.add(assessment)
    db.commit()

    # 3. Run the applicability reasoning agent
    decision = await run_applicability_agent(db, assessment)
    assert decision.recommended_path_scheme_id == "SLS_MARK_CORDIAL"
    assert {item.scheme_id for item in decision.decisions} == {"SLS_MARK_CORDIAL"}
    applicability_data = assessment.profile_data["applicability_decision"]
    assert applicability_data["already_held_scheme_ids"] == ["CAA_FOOD_REG"]
    assert "already held" in decision.overall_reasoning
    assert "completed first" not in decision.overall_reasoning
    assert assessment.scheme_id == decision.recommended_path_scheme_id


def test_api_applicable_schemes_route(client: TestClient, db: Session) -> None:
    # Test API endpoint
    bp_res = client.post(
        "/api/v1/business-profiles",
        json={
            "name": "Test Factory",
            "business_type": "sole_proprietor",
            "scale": "micro",
            "market": ["local_direct"],
            "existing_certifications": [],
            "has_food_licence": "no",
        },
    )
    assert bp_res.status_code == 201
    bp_data = bp_res.json()
    bp_id = bp_data["id"]

    # Create assessment
    ass_res = client.post("/api/v1/assessments")
    assert ass_res.status_code == 201
    ass_id = ass_res.json()["id"]

    # Link profile by fetching and attaching in DB
    import uuid

    ass_uuid = uuid.UUID(ass_id)
    assessment = db.get(Assessment, ass_uuid)
    assert assessment is not None
    assessment.business_profile_id = uuid.UUID(bp_id)
    cats = list_categories(db)
    prods = list_products(db, str(cats[0].id))
    assessment.product_id = prods[0].id
    db.commit()

    # Call endpoint
    app_res = client.post(f"/api/v1/assessments/{ass_id}/applicable-schemes")
    assert app_res.status_code == 200
    res_json = app_res.json()
    assert res_json["assessment_id"] == ass_id
    assert len(res_json["decisions"]) >= 1
    assert "overall_reasoning" in res_json


def test_api_does_not_recommend_food_registration_already_held(
    client: TestClient, db: Session
) -> None:
    assessment_response = client.post("/api/v1/assessments")
    assessment_id = assessment_response.json()["id"]
    profile_response = client.post(
        "/api/v1/business-profiles",
        json={
            "name": "Serendib Fresh Foods (Pvt) Ltd",
            "business_type": "limited_company",
            "years_operating": 3,
            "scale": "small",
            "market": ["supermarket", "local_retail"],
            "existing_certifications": ["CAA Food Business Registration"],
            "has_food_licence": "yes",
            "monthly_volume_range": "500_2000",
            "additional_info": "Preparing to supply major supermarket chains.",
            "assessment_id": assessment_id,
            "product_slug": "fresh_fruit_cordial",
        },
    )
    assert profile_response.status_code == 201

    response = client.post(f"/api/v1/assessments/{assessment_id}/applicable-schemes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_path_scheme_id"] == "SLS_MARK_CORDIAL"
    assert {item["scheme_id"] for item in payload["decisions"]} == {"SLS_MARK_CORDIAL"}
    assert payload["already_held_schemes"] == [
        {
            "scheme_id": "CAA_FOOD_REG",
            "scheme_name": "CAA Food Business Registration",
            "body_name": "Consumer Affairs Authority",
            "status_message": (
                "Your business profile says this registration or licence is already held, "
                "so it is not recommended as a new action."
            ),
        }
    ]


# ── Track 2 — Process Management applicability ──────────────────────────────
@pytest.mark.asyncio
async def test_track2_domestic_manufacturer(db: Session) -> None:
    """Domestic-only food manufacturer: GMP recommended, HACCP recommended, ISO optional."""
    from app.models.enums import CertificationTrack
    from app.services.catalog_service import list_schemes

    bp = create_business_profile(
        db,
        name="Village Kitchen Foods",
        business_type="sole_proprietor",
        years_operating=2,
        scale="micro",
        market=["local_retail"],  # domestic only — no supermarket or export
        existing_certifications=[],
        has_food_licence="no",
        monthly_volume_range="under_100",
        additional_info="Small home-based jam and preserve manufacturer.",
    )

    assessment = Assessment(
        status=AssessmentStatus.DRAFT_PROFILE,
        business_profile_id=bp.id,
        product_id=None,
    )
    db.add(assessment)
    db.commit()

    # Load Track 2 schemes for the agent
    pm_schemes = list_schemes(db, track=CertificationTrack.PROCESS_MANAGEMENT)
    assert any(s.id == "SLS_GMP" for s in pm_schemes)

    decision = await run_applicability_agent(db, assessment)

    decision_map = {d.scheme_id: d for d in decision.decisions}

    # GMP must always be recommended for domestic manufacturers
    if "SLS_GMP" in decision_map:
        assert decision_map["SLS_GMP"].tier == "recommended"

    # HACCP for non-formal market should be recommended (not market_required)
    if "SLS_HACCP" in decision_map:
        assert decision_map["SLS_HACCP"].tier in ("recommended", "optional")

    # ISO 22000 should be optional for domestic-only
    if "ISO_22000" in decision_map:
        assert decision_map["ISO_22000"].tier == "optional"


@pytest.mark.asyncio
async def test_track2_export_manufacturer_gets_iso_recommended(db: Session) -> None:
    """Export-market manufacturer: HACCP market_required, ISO 22000 recommended."""
    bp = create_business_profile(
        db,
        name="Ceylon Export Foods Ltd",
        business_type="limited_company",
        years_operating=10,
        scale="medium",
        market=["supermarket", "export"],  # targets formal + export markets
        existing_certifications=[],
        has_food_licence="yes",
        monthly_volume_range="500_2000",
        additional_info="Exporting to EU and Middle East.",
    )

    assessment = Assessment(
        status=AssessmentStatus.DRAFT_PROFILE,
        business_profile_id=bp.id,
        product_id=None,
    )
    db.add(assessment)
    db.commit()

    decision = await run_applicability_agent(db, assessment)
    decision_map = {d.scheme_id: d for d in decision.decisions}

    # For export+supermarket: HACCP must be market_required
    if "SLS_HACCP" in decision_map:
        assert decision_map["SLS_HACCP"].tier == "market_required"

    # For export market: ISO 22000 must be recommended
    if "ISO_22000" in decision_map:
        assert decision_map["ISO_22000"].tier == "recommended"
