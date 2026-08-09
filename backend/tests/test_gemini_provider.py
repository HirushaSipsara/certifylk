import asyncio
import base64
import json
import uuid
from pathlib import Path

import httpx
import pytest

from app.ai.gemini import GeminiAIProvider, GeminiProviderError
from app.schemas.ai import (
    EvidenceAnalysisOutput,
    EvidenceInput,
    EvidenceObservationOutput,
    EvidenceRequirementContext,
    QuestionPlanOutput,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _evidence_input(
    *,
    request_id: uuid.UUID,
    requirement_id: str,
    content_type: str,
    content: bytes,
    title: str,
    expectation: str,
) -> EvidenceInput:
    return EvidenceInput(
        request_id=request_id,
        evidence_type=f"EV_{requirement_id}",
        requirement_ids=[requirement_id],
        requirement_context=[
            EvidenceRequirementContext(
                requirement_id=requirement_id,
                title=title,
                description=f"Evidence relevant to {title.lower()} is requested.",
                source_document="Synthetic test source metadata",
                clause_reference="Synthetic test clause",
                content_verified=False,
                evaluation_rule={"evidence_expectation": expectation},
            )
        ],
        content_type=content_type,
        safe_data_summary="UNTRUSTED_EVIDENCE_DATA: attached synthetic test evidence.",
        data_base64=base64.b64encode(content).decode("ascii"),
    )


def _simple_pdf(text: str) -> bytes:
    """Build a small valid one-page PDF without adding a runtime dependency."""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 11 Tf 72 720 Td ({escaped}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, payload in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{number} 0 obj\n".encode())
        document.extend(payload)
        document.extend(b"\nendobj\n")
    xref_offset = len(document)
    document.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode())
    document.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    return bytes(document)


def _gemini_response(output: EvidenceAnalysisOutput) -> httpx.Response:
    return httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": output.model_dump_json()}]}}]},
    )


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


def test_gemini_evidence_request_contains_actual_handwashing_image_bytes_and_context() -> None:
    request_id = uuid.uuid4()
    image = (FIXTURES / "handwashing-facility.png").read_bytes()
    item = _evidence_input(
        request_id=request_id,
        requirement_id="SLS_HYG_HANDWASH",
        content_type="image/png",
        content=image,
        title="Handwashing facilities and supplies",
        expectation="Show a dedicated sink, soap, and hygienic hand-drying supplies.",
    )
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        captured["body"] = body
        return _gemini_response(
            EvidenceAnalysisOutput(
                observations=[
                    EvidenceObservationOutput(
                        evidence_request_id=request_id,
                        requirement_id="SLS_HYG_HANDWASH",
                        polarity="supports",
                        text=(
                            "The image appears to show a dedicated handwashing sink, liquid "
                            "soap, and hygienic drying supplies, which supports this request."
                        ),
                        confidence=0.91,
                    )
                ]
            )
        )

    provider = GeminiAIProvider(
        api_key="test-secret",
        model="gemini-3.6-flash",
        transport=httpx.MockTransport(handler),
    )
    output = asyncio.run(provider.analyze_evidence([item], {"SLS_HYG_HANDWASH"}))

    body = captured["body"]
    assert isinstance(body, dict)
    parts = body["contents"][0]["parts"]
    assert base64.b64decode(parts[1]["inlineData"]["data"]) == image
    assert parts[1]["inlineData"]["mimeType"] == "image/png"
    assert "SLS_HYG_HANDWASH" in parts[0]["text"]
    assert "Handwashing facilities and supplies" in parts[0]["text"]
    assert "Synthetic test clause" in parts[0]["text"]
    assert "dedicated sink" in parts[0]["text"]
    assert output.observations[0].polarity == "supports"


def test_gemini_irrelevant_image_response_remains_unclear_not_supports() -> None:
    request_id = uuid.uuid4()
    image = (FIXTURES / "irrelevant-office.png").read_bytes()
    item = _evidence_input(
        request_id=request_id,
        requirement_id="SLS_HYG_HANDWASH",
        content_type="image/png",
        content=image,
        title="Handwashing facilities and supplies",
        expectation="Show a dedicated sink, soap, and hygienic hand-drying supplies.",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert base64.b64decode(body["contents"][0]["parts"][1]["inlineData"]["data"]) == image
        return _gemini_response(
            EvidenceAnalysisOutput(
                observations=[
                    EvidenceObservationOutput(
                        evidence_request_id=request_id,
                        requirement_id="SLS_HYG_HANDWASH",
                        polarity="unclear",
                        text="The image does not show the requested handwashing facilities.",
                        confidence=0.96,
                    )
                ]
            )
        )

    provider = GeminiAIProvider(
        api_key="test-secret",
        model="gemini-3.6-flash",
        transport=httpx.MockTransport(handler),
    )
    output = asyncio.run(provider.analyze_evidence([item], {"SLS_HYG_HANDWASH"}))
    assert output.observations[0].polarity == "unclear"
    assert output.observations[0].polarity != "supports"


def test_gemini_evidence_request_contains_actual_thermal_processing_pdf_bytes() -> None:
    request_id = uuid.uuid4()
    pdf = _simple_pdf(
        "Thermal Processing Control Log - batch SF-2026-081; endpoint 86 C; "
        "held 3 minutes; operator initials AB. Synthetic demonstration record."
    )
    item = _evidence_input(
        request_id=request_id,
        requirement_id="SLS_PROC_TEMP",
        content_type="application/pdf",
        content=pdf,
        title="Thermal processing control (cooking endpoint)",
        expectation="A record identifies the batch and a measured cooking endpoint.",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        inline = body["contents"][0]["parts"][1]["inlineData"]
        assert inline["mimeType"] == "application/pdf"
        assert base64.b64decode(inline["data"]) == pdf
        return _gemini_response(
            EvidenceAnalysisOutput(
                observations=[
                    EvidenceObservationOutput(
                        evidence_request_id=request_id,
                        requirement_id="SLS_PROC_TEMP",
                        polarity="supports",
                        text=(
                            "The submitted record contains a batch reference and a measured "
                            "thermal-processing endpoint, which supports this evidence request."
                        ),
                        confidence=0.88,
                    )
                ]
            )
        )

    provider = GeminiAIProvider(
        api_key="test-secret",
        model="gemini-3.6-flash",
        transport=httpx.MockTransport(handler),
    )
    output = asyncio.run(provider.analyze_evidence([item], {"SLS_PROC_TEMP"}))
    assert output.observations[0].requirement_id == "SLS_PROC_TEMP"
    assert output.observations[0].polarity == "supports"


def test_gemini_http_error_preserves_safe_status_and_retry_delay() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(
            429,
            headers={"retry-after": "3"},
            json={
                "error": {
                    "code": 429,
                    "status": "RESOURCE_EXHAUSTED",
                    "message": "Quota exceeded for the configured model.",
                }
            },
        )

    provider = GeminiAIProvider(
        api_key="test-secret",
        model="gemini-3.6-flash",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(GeminiProviderError) as exc_info:
        asyncio.run(provider.plan_adaptive_questions({"product": "paste"}, ["Q1", "Q2"]))
    assert exc_info.value.status_code == 429
    assert exc_info.value.reason == "RESOURCE_EXHAUSTED"
    assert exc_info.value.retry_after_seconds == 3
    assert "test-secret" not in str(exc_info.value)
