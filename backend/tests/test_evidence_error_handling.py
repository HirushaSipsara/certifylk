import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models import EvidenceFile
from app.services.ai_service import run_with_validation


def test_missing_evidence_file_returns_400(client: TestClient, db_session: Session) -> None:
    """Verify missing evidence file on disk returns 400 AppError instead of unhandled 500."""
    created = client.post("/api/v1/assessments")
    assessment_id = created.json()["id"]

    profile = {
        "product_name": "Chilli paste",
        "food_category": "processed_food",
        "production_location": "home_kitchen",
        "production_scale": "small",
        "worker_range": "1_5",
        "packaging_type": "glass_bottle",
        "storage_method": "room_temperature",
        "shelf_life_range": "one_to_six_months",
        "existing_certification": "none",
        "production_record_frequency": "sometimes",
        "additional_information": "Small cooked batches",
    }
    saved = client.put(f"/api/v1/assessments/{assessment_id}/profile", json=profile)
    assert saved.status_code == 200
    adaptive = client.post(f"/api/v1/assessments/{assessment_id}/adaptive-plan")
    adaptive_questions = adaptive.json()["questions"]
    answers = [
        {"question_id": q["id"], "value": q["options"][0]["value"], "other_text": None}
        for q in adaptive_questions
    ]
    client.put(
        f"/api/v1/assessments/{assessment_id}/process",
        json={
            "steps": ["Extract juice", "Blend with sugar", "Pasteurize", "Bottle", "Store"],
            "adaptive_answers": answers,
        },
    )
    client.post(f"/api/v1/assessments/{assessment_id}/process-analysis")
    plan = client.post(f"/api/v1/assessments/{assessment_id}/evidence-plan")
    requests = plan.json()["requests"]

    # Upload a file for the first request
    req_id = requests[0]["id"]
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc` \x05\x00\x00\x04\x00\x01\x07\x05\xd3\xd2\x00\x00\x00\x00IEND\xaeB`\x82"
    upload = client.post(
        f"/api/v1/assessments/{assessment_id}/evidence/upload",
        data={"evidence_request_id": req_id},
        files={"file": ("workspace.png", png_bytes, "image/png")},
    )
    assert upload.status_code == 201

    # Mark remaining requests unavailable
    for req in requests[1:]:
        client.put(f"/api/v1/assessments/{assessment_id}/evidence/{req['id']}/unavailable")

    # Manually tamper with the database to point storage_key to a non-existent file
    file_record = (
        db_session.query(EvidenceFile).filter_by(evidence_request_id=uuid.UUID(req_id)).first()
    )
    assert file_record is not None
    file_record.storage_key = "non_existent_folder/missing_file.png"
    db_session.commit()

    # Post evidence analysis - should return HTTP 400 with evidence_file_missing
    response = client.post(f"/api/v1/assessments/{assessment_id}/evidence-analysis")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "evidence_file_missing"
    assert "was not found in storage" in data["error"]["message"]


@pytest.mark.asyncio
async def test_ai_provider_missing_key_fallback(db_session: Session) -> None:
    """Verify missing Gemini API key falls back to Mock provider when fallback is enabled."""
    bad_settings = Settings(ai_provider="gemini", gemini_api_key="", allow_ai_fallback=True)

    async def dummy_call(provider):
        return "ok"

    result = await run_with_validation(
        db_session,
        assessment_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        operation="test",
        call=dummy_call,
        settings=bad_settings,
    )
    assert result.output == "ok"
    assert result.provider == "mock"


@pytest.mark.asyncio
async def test_ai_provider_missing_key_raises_app_error_when_fallback_disabled(
    db_session: Session,
) -> None:
    """Verify missing Gemini API key raises AppError 500 when fallback is disabled."""
    bad_settings = Settings(ai_provider="gemini", gemini_api_key="", allow_ai_fallback=False)

    async def dummy_call(provider):
        return "ok"

    with pytest.raises(AppError) as exc_info:
        await run_with_validation(
            db_session,
            assessment_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            operation="test",
            call=dummy_call,
            settings=bad_settings,
        )
    assert exc_info.value.code == "ai_configuration_error"
    assert exc_info.value.status_code == 500
