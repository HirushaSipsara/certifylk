from fastapi.testclient import TestClient


def choose_answers(questions: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "question_id": question["id"],
            "value": question["options"][0]["value"],
            "other_text": None,
        }
        for question in questions
    ]


def test_complete_assessment_api_flow(client: TestClient) -> None:
    created = client.post("/api/v1/assessments")
    assert created.status_code == 201
    assessment_id = created.json()["id"]

    invalid = client.put(
        f"/api/v1/assessments/{assessment_id}/process",
        json={"steps": ["a", "b", "c", "", ""], "adaptive_answers": []},
    )
    assert invalid.status_code == 409
    assert invalid.json()["error"]["code"] == "invalid_transition"

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
    assert adaptive.status_code == 200
    adaptive_questions = adaptive.json()["questions"]
    assert 2 <= len(adaptive_questions) <= 5

    process = client.put(
        f"/api/v1/assessments/{assessment_id}/process",
        json={
            "steps": ["Buy ingredients", "Wash ingredients", "Cook", "Fill jars", "Store"],
            "adaptive_answers": choose_answers(adaptive_questions),
        },
    )
    assert process.status_code == 200
    assert client.post(f"/api/v1/assessments/{assessment_id}/process-analysis").status_code == 200
    plan = client.post(f"/api/v1/assessments/{assessment_id}/evidence-plan")
    assert plan.status_code == 200
    requests = plan.json()["requests"]
    assert sum(item["kind"] == "photo" for item in requests) <= 5
    assert sum(item["kind"] == "document" for item in requests) <= 2
    for index, request in enumerate(requests):
        assert request["current_state_question"]
        current_state = client.put(
            f"/api/v1/assessments/{assessment_id}/evidence/{request['id']}/self-assessment",
            json={"value": "no" if index == 0 else "yes"},
        )
        assert current_state.status_code == 200
        assert current_state.json()["value"] == ("no" if index == 0 else "yes")
        unavailable = client.put(
            f"/api/v1/assessments/{assessment_id}/evidence/{request['id']}/unavailable"
        )
        assert unavailable.status_code == 200

    evidence_analysis = client.post(f"/api/v1/assessments/{assessment_id}/evidence-analysis")
    assert evidence_analysis.status_code == 200
    assert evidence_analysis.json()["review_status"] == "not_requested"
    clarifications = client.post(f"/api/v1/assessments/{assessment_id}/clarification-plan")
    assert clarifications.status_code == 200
    clarification_questions = clarifications.json()["questions"]
    assert 3 <= len(clarification_questions) <= 5
    saved_clarifications = client.put(
        f"/api/v1/assessments/{assessment_id}/clarifications",
        json={"answers": choose_answers(clarification_questions)},
    )
    assert saved_clarifications.status_code == 200
    completed = client.post(f"/api/v1/assessments/{assessment_id}/complete")
    assert completed.status_code == 200, completed.text
    result = client.get(f"/api/v1/assessments/{assessment_id}/result")
    assert result.status_code == 200
    body = result.json()
    assert 0 <= body["overall_score"] <= 100
    assert body["strengths"]
    assert body["gaps"]
    assert body["roadmap"]
    assert body["roadmap"][0]["one_time_cost"]["currency"] == "LKR"
    assert "does not issue" in body["disclaimer"]
    assert result.headers["X-Request-ID"]


def test_sample_endpoint_is_complete(client: TestClient) -> None:
    sample = client.post("/api/v1/assessments/sample")
    assert sample.status_code == 201, sample.text
    body = sample.json()
    assert body["status"] == "completed"
    result = client.get(f"/api/v1/assessments/{body['id']}/result")
    assert result.status_code == 200
    assert len(result.json()["strengths"]) >= 2
