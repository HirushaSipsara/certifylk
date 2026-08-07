import re
from typing import Any

from app.schemas.ai import (
    ApplicabilityDecisionOutput,
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
    SchemeDecision,
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

    async def plan_applicable_schemes(
        self,
        business_profile: dict[str, Any],
        product: dict[str, Any],
        schemes: list[dict[str, Any]],
    ) -> ApplicabilityDecisionOutput:
        """Deterministic mock: handles both Track 1 (product quality) and Track 2 (process management)."""
        supplied_ids = {s["id"] for s in schemes}
        decisions: list[SchemeDecision] = []
        recommended_id: str | None = None

        market: list[str] = business_profile.get("market", [])
        targets_formal_market = any(m in market for m in ("supermarket", "export", "institutional"))
        targets_export = "export" in market

        # Determine track context from supplied scheme IDs
        is_process_track = any(sid in supplied_ids for sid in ("SLS_GMP", "SLS_HACCP", "ISO_22000"))

        for scheme in schemes:
            sid = scheme["id"]

            # ── Track 1 — Product Quality schemes ──────────────────────────────
            if sid == "CAA_FOOD_REG":
                decisions.append(
                    SchemeDecision(
                        scheme_id=sid,
                        tier="mandatory",
                        confidence=0.99,
                        reasoning=(
                            "Registration under the Food Act No. 26 of 1980 is legally required "
                            "for all food manufacturers selling in Sri Lanka, regardless of scale or market."
                        ),
                        source_reference="applicability_rule.mandatory_note — Food Act No. 26 of 1980",
                    )
                )
                if recommended_id is None:
                    recommended_id = sid

            elif sid == "SLS_MARK_CORDIAL":
                if targets_formal_market:
                    decisions.append(
                        SchemeDecision(
                            scheme_id=sid,
                            tier="market_required",
                            confidence=0.92,
                            reasoning=(
                                "Your target market includes supermarkets or export channels that "
                                "routinely require the SLS Mark as a supplier qualification criterion."
                            ),
                            source_reference=(
                                "applicability_rule.mandatory_note — Required by most supermarket "
                                "chains and all government institutional buyers."
                            ),
                        )
                    )
                    recommended_id = sid
                else:
                    decisions.append(
                        SchemeDecision(
                            scheme_id=sid,
                            tier="recommended",
                            confidence=0.75,
                            reasoning=(
                                "The SLS Mark is not yet required by your current markets, "
                                "but obtaining it will open access to supermarket and institutional buyers."
                            ),
                            source_reference="applicability_rule.mandatory_note — SLS Mark broadens market access.",
                        )
                    )

            # ── Track 2 — Process Management schemes ───────────────────────────
            elif sid == "SLS_GMP":
                # GMP is recommended for every food manufacturer as the baseline
                decisions.append(
                    SchemeDecision(
                        scheme_id=sid,
                        tier="recommended",
                        confidence=0.95,
                        reasoning=(
                            "GMP Certification is the essential baseline for any food manufacturing operation. "
                            "It demonstrates systematic control of your premises, personnel, equipment, and "
                            "processes, and is required by most supermarket chains alongside product marks."
                        ),
                        source_reference="applicability_rule.note — Recommended for all food manufacturers.",
                    )
                )
                if recommended_id is None or (is_process_track and recommended_id != "SLS_GMP"):
                    recommended_id = sid

            elif sid == "SLS_HACCP":
                if targets_formal_market:
                    decisions.append(
                        SchemeDecision(
                            scheme_id=sid,
                            tier="market_required",
                            confidence=0.93,
                            reasoning=(
                                "HACCP Certification is required by your target market. "
                                "All major Sri Lankan supermarket chains, government institutional food "
                                "contracts, and export markets mandate HACCP as a prerequisite for supply. "
                                "It is also the foundation of any ISO 22000 implementation."
                            ),
                            source_reference=(
                                "applicability_rule.market — supermarket, institutional, export."
                            ),
                        )
                    )
                    # HACCP becomes the primary recommended path when targeting formal markets
                    recommended_id = sid
                else:
                    decisions.append(
                        SchemeDecision(
                            scheme_id=sid,
                            tier="recommended",
                            confidence=0.72,
                            reasoning=(
                                "While HACCP is not immediately required by your current markets, "
                                "implementing it will systematically reduce food safety risk and "
                                "prepare you to access supermarket and export channels in future."
                            ),
                            source_reference="applicability_rule.market — proactive recommendation.",
                        )
                    )

            elif sid == "ISO_22000":
                if targets_export:
                    decisions.append(
                        SchemeDecision(
                            scheme_id=sid,
                            tier="recommended",
                            confidence=0.88,
                            reasoning=(
                                "ISO 22000:2018 is strongly recommended given your export market target. "
                                "Most regulated export markets (EU, US, Australia, Middle East) and global "
                                "retail buyers require or strongly prefer this internationally recognised "
                                "Food Safety Management System standard. It integrates your GMP and HACCP "
                                "programmes into a full FSMS with management review and continuous improvement."
                            ),
                            source_reference="applicability_rule.note — Recommended for export to regulated markets.",
                        )
                    )
                else:
                    decisions.append(
                        SchemeDecision(
                            scheme_id=sid,
                            tier="optional",
                            confidence=0.60,
                            reasoning=(
                                "ISO 22000 is optional for your current domestic market profile. "
                                "If you plan to enter export markets in future, starting with GMP and HACCP "
                                "now will position you to achieve ISO 22000 with less incremental effort."
                            ),
                            source_reference="applicability_rule.note — optional domestically; recommended for export.",
                        )
                    )

            elif sid in supplied_ids:
                # Any other supplied scheme — mark as optional with low confidence
                decisions.append(
                    SchemeDecision(
                        scheme_id=sid,
                        tier="optional",
                        confidence=0.50,
                        reasoning=(
                            f"This scheme ({scheme.get('name', sid)}) may become relevant "
                            "as your business scales or diversifies markets."
                        ),
                        source_reference="applicability_rule — optional for current profile",
                    )
                )

        if not decisions:
            # Fallback — should not happen in normal flow
            decisions.append(
                SchemeDecision(
                    scheme_id=schemes[0]["id"] if schemes else "UNKNOWN",
                    tier="optional",
                    confidence=0.30,
                    reasoning="Insufficient information to determine applicability. Please refine your profile.",
                    source_reference="applicability_rule — indeterminate",
                )
            )

        # Build overall reasoning for the response
        if is_process_track:
            overall = "Based on your business profile, GMP Certification is recommended as your foundation. "
            if targets_formal_market:
                overall += "HACCP Certification is required for your supermarket or export market targets. "
            if targets_export:
                overall += "ISO 22000:2018 is strongly recommended to meet your export market requirements."
            else:
                overall += "ISO 22000 is available as an optional international standard if you plan to export."
        else:
            overall = (
                "Based on the submitted business profile and product, two certification "
                "actions are identified. CAA registration is legally required and should be "
                "completed first. The SLS Mark is the recommended next step to unlock "
                "supermarket and institutional market access."
            )

        return ApplicabilityDecisionOutput(
            decisions=decisions,
            overall_reasoning=overall,
            recommended_path_scheme_id=recommended_id,
        )
