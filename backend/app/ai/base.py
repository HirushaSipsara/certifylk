from typing import Any, Protocol

from app.schemas.ai import (
    EvidenceAnalysisOutput,
    EvidenceInput,
    ProcessExtractionOutput,
    QuestionPlanOutput,
    RoadmapExplanationInput,
    RoadmapExplanationsOutput,
)


class AIProvider(Protocol):
    name: str
    model: str

    async def plan_adaptive_questions(
        self, profile: dict[str, Any], candidate_question_ids: list[str]
    ) -> QuestionPlanOutput: ...

    async def extract_process(
        self, steps: list[str], adaptive_answers: dict[str, str]
    ) -> ProcessExtractionOutput: ...

    async def analyze_evidence(
        self, evidence: list[EvidenceInput], allowed_requirement_ids: set[str]
    ) -> EvidenceAnalysisOutput: ...

    async def plan_clarifications(
        self, context: dict[str, Any], candidate_question_ids: list[str]
    ) -> QuestionPlanOutput: ...

    async def explain_roadmap(
        self, items: list[RoadmapExplanationInput]
    ) -> RoadmapExplanationsOutput: ...
