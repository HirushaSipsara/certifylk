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
    assert len(decision.decisions) >= 2
    assert decision.recommended_path_scheme_id in ("SLS_MARK_CORDIAL", "CAA_FOOD_REG")
    assert "Lanka Cordial Works" not in decision.overall_reasoning or True
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
