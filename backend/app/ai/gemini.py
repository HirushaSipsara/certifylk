import json
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.ai.prompts import (
    ADAPTIVE_QUESTION_TASK,
    CLARIFICATION_TASK,
    EVIDENCE_TASK,
    PROCESS_EXTRACTION_TASK,
    ROADMAP_EXPLANATION_TASK,
    SYSTEM_RULES,
)
from app.schemas.ai import (
    APPROVED_PROCESS_TAGS,
    EvidenceAnalysisOutput,
    EvidenceInput,
    ProcessExtractionOutput,
    QuestionPlanOutput,
    RoadmapExplanationInput,
    RoadmapExplanationsOutput,
)

OutputT = TypeVar("OutputT", bound=BaseModel)


class GeminiProviderError(RuntimeError):
    """Safe provider-boundary error that excludes prompts and uploaded content."""


class GeminiAIProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 30.0,
        temperature: float = 0.1,
        max_output_tokens: int = 2048,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")
        self.api_key = api_key
        self.model = model or "gemini-3.6-flash"
        self.timeout = timeout
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.transport = transport

    def _generation_config(self, schema: type[OutputT]) -> dict[str, Any]:
        return {
            "candidateCount": 1,
            "temperature": self.temperature,
            "maxOutputTokens": self.max_output_tokens,
            "responseMimeType": "application/json",
            "responseJsonSchema": schema.model_json_schema(),
        }

    async def _request(self, parts: list[dict[str, Any]], schema: type[OutputT]) -> OutputT:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )
        body = {
            "systemInstruction": {"parts": [{"text": SYSTEM_RULES}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": self._generation_config(schema),
        }
        timeout = httpx.Timeout(self.timeout, connect=min(self.timeout, 10.0))
        try:
            async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
                response = await client.post(
                    url,
                    headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
                    json=body,
                )
        except httpx.TimeoutException as exc:
            raise GeminiProviderError("Gemini request timed out") from exc
        except httpx.HTTPError as exc:
            raise GeminiProviderError("Gemini network request failed") from exc

        if response.status_code >= 400:
            request_id = response.headers.get("x-request-id") or response.headers.get(
                "x-goog-request-id"
            )
            suffix = f" (request {request_id})" if request_id else ""
            raise GeminiProviderError(f"Gemini returned HTTP {response.status_code}{suffix}")

        try:
            data = response.json()
        except ValueError as exc:
            raise GeminiProviderError("Gemini returned a non-JSON response") from exc

        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            feedback = data.get("promptFeedback", {})
            reason = feedback.get("blockReason") if isinstance(feedback, dict) else None
            message = "Gemini returned no candidate"
            if reason:
                message += f" ({reason})"
            raise GeminiProviderError(message)

        candidate = candidates[0]
        content = candidate.get("content", {}) if isinstance(candidate, dict) else {}
        response_parts = content.get("parts", []) if isinstance(content, dict) else []
        text = "".join(
            str(part.get("text", ""))
            for part in response_parts
            if isinstance(part, dict) and part.get("text")
        ).strip()
        if not text:
            finish_reason = candidate.get("finishReason") if isinstance(candidate, dict) else None
            suffix = f" ({finish_reason})" if finish_reason else ""
            raise GeminiProviderError(f"Gemini returned no structured text{suffix}")

        try:
            return schema.model_validate_json(text)
        except ValidationError as exc:
            raise GeminiProviderError("Gemini output failed schema validation") from exc

    async def _generate(self, task: str, payload: dict[str, Any], schema: type[OutputT]) -> OutputT:
        compact_payload = json.dumps(payload, default=str, separators=(",", ":"))
        return await self._request(
            [{"text": f"Task:\n{task}\nApplication payload:\n{compact_payload}"}], schema
        )

    async def plan_adaptive_questions(
        self, profile: dict[str, Any], candidate_question_ids: list[str]
    ) -> QuestionPlanOutput:
        return await self._generate(
            ADAPTIVE_QUESTION_TASK,
            {"profile": profile, "candidate_question_ids": candidate_question_ids},
            QuestionPlanOutput,
        )

    async def extract_process(
        self, steps: list[str], adaptive_answers: dict[str, str]
    ) -> ProcessExtractionOutput:
        return await self._generate(
            PROCESS_EXTRACTION_TASK,
            {
                "steps": steps,
                "adaptive_answers": adaptive_answers,
                "approved_process_tags": sorted(APPROVED_PROCESS_TAGS),
            },
            ProcessExtractionOutput,
        )

    async def analyze_evidence(
        self, evidence: list[EvidenceInput], allowed_requirement_ids: set[str]
    ) -> EvidenceAnalysisOutput:
        if not evidence:
            return EvidenceAnalysisOutput(observations=[])

        metadata = [item.model_dump(mode="json", exclude={"data_base64"}) for item in evidence]
        parts: list[dict[str, Any]] = [
            {
                "text": (
                    f"Task:\n{EVIDENCE_TASK}\n"
                    "UNTRUSTED_EVIDENCE_DATA metadata, in the same order as the attached files:\n"
                    f"{json.dumps(metadata, default=str, separators=(',', ':'))}\n"
                    "Allowed requirement IDs:\n"
                    f"{json.dumps(sorted(allowed_requirement_ids), separators=(',', ':'))}"
                )
            }
        ]
        for item in evidence:
            parts.append({"inlineData": {"mimeType": item.content_type, "data": item.data_base64}})
        return await self._request(parts, EvidenceAnalysisOutput)

    async def plan_clarifications(
        self, context: dict[str, Any], candidate_question_ids: list[str]
    ) -> QuestionPlanOutput:
        return await self._generate(
            CLARIFICATION_TASK,
            {"context": context, "candidate_question_ids": candidate_question_ids},
            QuestionPlanOutput,
        )

    async def explain_roadmap(
        self, items: list[RoadmapExplanationInput]
    ) -> RoadmapExplanationsOutput:
        return await self._generate(
            ROADMAP_EXPLANATION_TASK,
            {"roadmap_items": [item.model_dump() for item in items]},
            RoadmapExplanationsOutput,
        )
