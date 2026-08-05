import re
from typing import Any

from app.schemas.ai import (
    EvidenceAnalysisOutput,
    EvidenceInput,
    EvidenceObservationOutput,
    ProcessExtractionOutput,
    ProcessStageOutput,
    ProcessTag,
    QuestionPlanOutput,
    RoadmapExplanationInput,
    RoadmapExplanationOutput,
    RoadmapExplanationsOutput,
)


class MockAIProvider:
    name = "mock"
    model = "deterministic-v1"

    async def plan_adaptive_questions(
        self, profile: dict[str, Any], candidate_question_ids: list[str]
    ) -> QuestionPlanOutput:
        count = min(5, max(2, len(candidate_question_ids)))
        return QuestionPlanOutput(
            question_ids=candidate_question_ids[:count],
            reason="Selected the highest-priority approved questions for this product profile.",
        )

    async def extract_process(
        self, steps: list[str], adaptive_answers: dict[str, str]
    ) -> ProcessExtractionOutput:
        del adaptive_answers
        stages: list[ProcessStageOutput] = []
        uncertainties: list[str] = []
        patterns: list[tuple[str, str, list[ProcessTag]]] = [
            (
                r"purchase|receive|buy|ingredient",
                "Ingredient receiving",
                ["receiving", "supplier_control"],
            ),
            (r"wash", "Washing", ["washing", "preparation"]),
            (r"prepare|cut|mix|grind", "Preparation", ["preparation"]),
            (r"cook|heat|boil|fry", "Cooking", ["cooking"]),
            (r"cool", "Cooling", ["cooling"]),
            (r"fill|bottle|pack", "Filling and packaging", ["filling", "packaging"]),
            (r"store|distribut|deliver", "Storage and distribution", ["storage", "distribution"]),
        ]
        for position, text in enumerate(steps, start=1):
            if not text.strip():
                continue
            name = "Production step"
            tags: list[ProcessTag] = ["preparation"]
            for pattern, candidate_name, candidate_tags in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    name, tags = candidate_name, candidate_tags
                    break
            stages.append(
                ProcessStageOutput(position=position, name=name, tags=tags, confidence=0.92)
            )
        if any("cooking" in stage.tags for stage in stages):
            uncertainties.append("Confirm how the cooking endpoint is measured and recorded.")
        return ProcessExtractionOutput(stages=stages, uncertainties=uncertainties)

    async def analyze_evidence(
        self, evidence: list[EvidenceInput], allowed_requirement_ids: set[str]
    ) -> EvidenceAnalysisOutput:
        observations: list[EvidenceObservationOutput] = []
        supportive_types = {"production_area", "handwashing_area", "ingredient_storage"}
        for item in evidence:
            for requirement_id in item.requirement_ids[:2]:
                if requirement_id not in allowed_requirement_ids:
                    continue
                supports = item.evidence_type in supportive_types
                observations.append(
                    EvidenceObservationOutput(
                        evidence_request_id=item.request_id,
                        requirement_id=requirement_id,
                        polarity="supports" if supports else "unclear",
                        text=(
                            "The submitted item provides visible supporting context for this practice."
                            if supports
                            else "The submitted item is relevant, but the required detail is not clear enough to confirm."
                        ),
                        confidence=0.82 if supports else 0.45,
                    )
                )
        return EvidenceAnalysisOutput(observations=observations)

    async def plan_clarifications(
        self, context: dict[str, Any], candidate_question_ids: list[str]
    ) -> QuestionPlanOutput:
        del context
        count = min(5, max(3, len(candidate_question_ids)))
        return QuestionPlanOutput(
            question_ids=candidate_question_ids[:count],
            reason="Selected approved high-priority questions not yet resolved by submitted evidence.",
        )

    async def explain_roadmap(
        self, items: list[RoadmapExplanationInput]
    ) -> RoadmapExplanationsOutput:
        return RoadmapExplanationsOutput(
            explanations=[
                RoadmapExplanationOutput(
                    recommendation_id=item.recommendation_id,
                    explanation=(
                        f"This action addresses {', '.join(item.affected_titles[:2]).lower()}. "
                        f"Start by {item.implementation_steps[0].lower()}."
                    ),
                )
                for item in items
            ]
        )
