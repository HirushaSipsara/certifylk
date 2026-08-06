import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import MockAIProvider
from app.api.v1 import routes as routes_module
from app.models import AIRun, EvidenceObservation, Requirement
from app.models.enums import ObservationPolarity, RequirementStatus
from app.schemas.ai import (
    EvidenceAnalysisOutput,
    EvidenceInput,
    EvidenceObservationOutput,
    ProcessExtractionOutput,
)
from app.services import ai_service
from app.services.requirement_engine import evaluate_requirement
from app.storage import LocalStorageProvider


class ConcernEvidenceAIProvider(MockAIProvider):
    """Test-only provider preserving Mock behavior except for uploaded evidence polarity."""

    async def analyze_evidence(
        self, evidence: list[EvidenceInput], allowed_requirement_ids: set[str]
    ) -> EvidenceAnalysisOutput:
        if not evidence:
            return EvidenceAnalysisOutput(observations=[])
        item = evidence[0]
        requirement_id = next(
            candidate for candidate in item.requirement_ids if candidate in allowed_requirement_ids
        )
        return EvidenceAnalysisOutput(
            observations=[
                EvidenceObservationOutput(
                    evidence_request_id=item.request_id,
                    requirement_id=requirement_id,
                    polarity="concern",
                    text="The submitted test evidence shows a concern requiring follow-up.",
                    confidence=0.91,
                )
            ]
        )


class FailingProcessGeminiProvider(MockAIProvider):
    name = "gemini"
    model = "test-failing-gemini"

    async def extract_process(
        self, steps: list[str], adaptive_answers: dict[str, str]
    ) -> ProcessExtractionOutput:
        del steps, adaptive_answers
        raise RuntimeError("Synthetic provider failure")


def choose_answers(questions: list[dict[str, Any]]) -> list[dict[str, object]]:
    return [
        {
            "question_id": question["id"],
            "value": question["options"][0]["value"],
            "other_text": None,
        }
        for question in questions
    ]


@pytest.fixture()
def concern_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ConcernEvidenceAIProvider:
    provider = ConcernEvidenceAIProvider()
    monkeypatch.setattr(ai_service, "get_ai_provider", lambda settings=None: provider)
    storage = LocalStorageProvider(tmp_path / "uploads")
    monkeypatch.setattr(routes_module, "get_storage_provider", lambda: storage)
    return provider


def test_concern_observation_api_persistence_evaluation_and_score_baseline(
    client: TestClient,
    db: Session,
    concern_provider: ConcernEvidenceAIProvider,
) -> None:
    del concern_provider
    created = client.post("/api/v1/assessments")
    assessment_id = created.json()["id"]
    assessment_uuid = uuid.UUID(assessment_id)
    profile = {
        "product_name": "Chilli paste concern test",
        "food_category": "processed_food",
        "production_location": "home_kitchen",
        "production_scale": "small",
        "worker_range": "1_5",
        "packaging_type": "glass_bottle",
        "storage_method": "room_temperature",
        "shelf_life_range": "one_to_six_months",
        "existing_certification": "none",
        "production_record_frequency": "sometimes",
        "additional_information": "Synthetic integration-test evidence only.",
    }
    assert (
        client.put(f"/api/v1/assessments/{assessment_id}/profile", json=profile).status_code == 200
    )
    adaptive = client.post(f"/api/v1/assessments/{assessment_id}/adaptive-plan")
    assert adaptive.status_code == 200
    process = client.put(
        f"/api/v1/assessments/{assessment_id}/process",
        json={
            "steps": ["Buy", "Wash", "Cook", "Fill bottles", "Store"],
            "adaptive_answers": choose_answers(adaptive.json()["questions"]),
        },
    )
    assert process.status_code == 200
    process_analysis = client.post(f"/api/v1/assessments/{assessment_id}/process-analysis")
    assert process_analysis.status_code == 200
    assert process_analysis.json()["provider"] == "mock"
    assert process_analysis.json()["fallback_used"] is False

    plan = client.post(f"/api/v1/assessments/{assessment_id}/evidence-plan")
    assert plan.status_code == 200
    requests = plan.json()["requests"]
    uploaded_request = requests[0]
    upload = client.post(
        f"/api/v1/assessments/{assessment_id}/evidence/upload",
        data={"evidence_request_id": uploaded_request["id"]},
        files={"file": ("production-area.png", b"\x89PNG\r\n\x1a\nsynthetic", "image/png")},
    )
    assert upload.status_code == 201, upload.text
    for request in requests[1:]:
        unavailable = client.put(
            f"/api/v1/assessments/{assessment_id}/evidence/{request['id']}/unavailable"
        )
        assert unavailable.status_code == 200

    response = client.post(f"/api/v1/assessments/{assessment_id}/evidence-analysis")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["provider"] == "mock"
    assert body["fallback_used"] is False
    assert len(body["observations"]) == 1
    assert body["observations"][0]["polarity"] == "concern"
    assert body["observations"][0]["polarity"] != "supports"

    runs = list(
        db.scalars(
            select(AIRun).where(
                AIRun.assessment_id == assessment_uuid,
                AIRun.operation == "analyze_evidence",
            )
        )
    )
    assert len(runs) == 1
    run = runs[0]
    assert run.provider == body["provider"] == "mock"
    assert run.fallback_used is body["fallback_used"] is False
    assert run.success is True

    observation = db.scalar(
        select(EvidenceObservation).where(EvidenceObservation.assessment_id == assessment_uuid)
    )
    assert observation is not None
    assert observation.polarity == ObservationPolarity.CONCERN
    assert observation.polarity != ObservationPolarity.SUPPORTS
    assert str(observation.id) == body["observations"][0]["id"]

    requirement = db.get(Requirement, observation.requirement_id)
    assert requirement is not None
    evaluated = evaluate_requirement(
        requirement,
        answers={},
        profile={},
        non_empty_process_steps=0,
        observations=[
            {
                "id": str(observation.id),
                "requirement_id": observation.requirement_id,
                "polarity": observation.polarity.value,
                "confidence": observation.confidence,
            }
        ],
    )
    assert evaluated.status == RequirementStatus.GAP
    assert evaluated.multiplier == 0
    assert evaluated.rationale == "Submitted evidence contains a clear concern about this practice."
    assert f"evidence:{observation.id}" in evaluated.evidence_references

    sample = client.post("/api/v1/assessments/sample")
    assert sample.status_code == 201
    sample_result = client.get(f"/api/v1/assessments/{sample.json()['id']}/result")
    assert sample_result.status_code == 200
    assert sample_result.json()["overall_score_raw"] == "32.0000"
    assert sample_result.json()["overall_score"] == 32


def test_process_response_reports_confirmed_fallback_from_exact_run(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FailingProcessGeminiProvider()
    monkeypatch.setattr(ai_service, "get_ai_provider", lambda settings=None: provider)
    created = client.post("/api/v1/assessments")
    assessment_id = created.json()["id"]
    assessment_uuid = uuid.UUID(assessment_id)
    profile = {
        "product_name": "Fallback test product",
        "food_category": "processed_food",
        "production_location": "home_kitchen",
        "production_scale": "small",
        "worker_range": "1_5",
        "packaging_type": "glass_bottle",
        "storage_method": "room_temperature",
        "shelf_life_range": "one_to_six_months",
        "existing_certification": "none",
        "production_record_frequency": "sometimes",
        "additional_information": "Synthetic fallback test.",
    }
    assert (
        client.put(f"/api/v1/assessments/{assessment_id}/profile", json=profile).status_code == 200
    )
    adaptive = client.post(f"/api/v1/assessments/{assessment_id}/adaptive-plan")
    assert adaptive.status_code == 200
    saved = client.put(
        f"/api/v1/assessments/{assessment_id}/process",
        json={
            "steps": ["Buy", "Wash", "Cook", "Fill bottles", "Store"],
            "adaptive_answers": choose_answers(adaptive.json()["questions"]),
        },
    )
    assert saved.status_code == 200

    response = client.post(f"/api/v1/assessments/{assessment_id}/process-analysis")
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
    assert response.json()["fallback_used"] is True

    runs = list(
        db.scalars(
            select(AIRun)
            .where(
                AIRun.assessment_id == assessment_uuid,
                AIRun.operation == "extract_process",
            )
            .order_by(AIRun.created_at, AIRun.id)
        )
    )
    assert len(runs) == 3
    assert all(run.provider == "gemini" and not run.success for run in runs[:2])
    assert runs[-1].provider == response.json()["provider"] == "mock"
    assert runs[-1].fallback_used is response.json()["fallback_used"] is True
    assert runs[-1].success is True
