import asyncio
import json

import httpx
import pytest

from app.ai.gemini import GeminiAIProvider, GeminiProviderError
from app.schemas.ai import QuestionPlanOutput


def test_gemini_uses_backend_header_and_structured_output_schema() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["api_key"] = request.headers.get("x-goog-api-key")
        captured["body"] = json.loads(request.content)
        model_output = QuestionPlanOutput(
            question_ids=["Q1", "Q2"], reason="These approved questions reduce uncertainty."
        ).model_dump_json()
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": model_output}]}}]},
        )

    provider = GeminiAIProvider(
        api_key="test-secret",
        model="gemini-3.6-flash",
        transport=httpx.MockTransport(handler),
    )
    output = asyncio.run(provider.plan_adaptive_questions({"product": "paste"}, ["Q1", "Q2"]))

    assert output.question_ids == ["Q1", "Q2"]
    assert captured["api_key"] == "test-secret"
    assert "test-secret" not in str(captured["url"])
    body = captured["body"]
    assert isinstance(body, dict)
    config = body["generationConfig"]
    assert config["responseMimeType"] == "application/json"
    assert config["responseJsonSchema"] == QuestionPlanOutput.model_json_schema()
    assert config["candidateCount"] == 1


def test_gemini_blocked_response_becomes_safe_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})

    provider = GeminiAIProvider(
        api_key="test-secret",
        model="gemini-3.6-flash",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(GeminiProviderError, match="no candidate"):
        asyncio.run(provider.plan_adaptive_questions({"product": "paste"}, ["Q1", "Q2"]))


def test_empty_evidence_avoids_a_network_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"Unexpected Gemini request: {request.url}")

    provider = GeminiAIProvider(
        api_key="test-secret",
        model="gemini-3.6-flash",
        transport=httpx.MockTransport(handler),
    )
    output = asyncio.run(provider.analyze_evidence([], set()))
    assert output.observations == []
