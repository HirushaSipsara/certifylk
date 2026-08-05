from dataclasses import dataclass
from decimal import Decimal

from app.core.errors import ConfigurationError
from app.models import CostItem, Recommendation
from app.models.enums import RequirementStatus
from app.services.requirement_engine import EvaluatedRequirement
from app.services.scoring_engine import project_score_after_actions


@dataclass
class RoadmapDraft:
    recommendation: Recommendation
    cost: CostItem
    affected: list[EvaluatedRequirement]
    tier: int
    gain: Decimal = Decimal("0")
    projected_score: Decimal = Decimal("0")


def map_gaps_to_recommendations(
    evaluations: list[EvaluatedRequirement],
    recommendations: list[Recommendation],
    costs: list[CostItem],
) -> list[RoadmapDraft]:
    uncovered = {
        item.requirement_id: item
        for item in evaluations
        if item.status
        in {RequirementStatus.GAP, RequirementStatus.PARTIAL, RequirementStatus.UNKNOWN}
    }
    cost_by_recommendation = {item.recommendation_id: item for item in costs}
    drafts: list[RoadmapDraft] = []
    for recommendation in recommendations:
        if not recommendation.active:
            continue
        affected = [
            uncovered[requirement_id]
            for requirement_id in recommendation.requirement_ids
            if requirement_id in uncovered
        ]
        if not affected:
            continue
        cost = cost_by_recommendation.get(recommendation.id)
        if cost is None:
            raise ConfigurationError(f"No catalogue cost exists for {recommendation.id}.")
        drafts.append(
            RoadmapDraft(
                recommendation=recommendation,
                cost=cost,
                affected=affected,
                tier=_priority_tier(recommendation, cost, affected),
            )
        )
    return drafts


def _priority_tier(
    recommendation: Recommendation,
    cost: CostItem,
    affected: list[EvaluatedRequirement],
) -> int:
    if any(item.safety_critical and item.status == RequirementStatus.GAP for item in affected):
        return 1
    uncovered_weight = sum(
        (item.weight * (Decimal("1") - item.multiplier) for item in affected), Decimal("0")
    )
    if max(item.weight for item in affected) >= Decimal("5"):
        return 2
    if cost.one_time_max <= 5000 and uncovered_weight >= Decimal("2"):
        return 3
    if any(item.category == "documentation_records" for item in affected):
        return 4
    if recommendation.is_capex:
        return 5
    return 4


def calculate_recommendation_gain(draft: RoadmapDraft, already_covered: set[str]) -> Decimal:
    gain = Decimal("0")
    for item in draft.affected:
        if item.requirement_id in already_covered:
            continue
        gain += item.weight * (Decimal("1") - item.multiplier)
        already_covered.add(item.requirement_id)
    return gain.quantize(Decimal("0.001"))


def rank_recommendations(drafts: list[RoadmapDraft]) -> list[RoadmapDraft]:
    return sorted(
        drafts,
        key=lambda draft: (
            draft.tier,
            -sum(item.weight * (Decimal("1") - item.multiplier) for item in draft.affected),
            -draft.recommendation.priority_base,
            draft.cost.one_time_max,
            draft.recommendation.id,
        ),
    )


def calculate_cost_summary(drafts: list[RoadmapDraft]) -> dict[str, object]:
    return {
        "one_time_min": sum(item.cost.one_time_min for item in drafts),
        "one_time_max": sum(item.cost.one_time_max for item in drafts),
        "recurring_min": sum(item.cost.recurring_min for item in drafts),
        "recurring_max": sum(item.cost.recurring_max for item in drafts),
        "currency": "LKR",
    }


def build_roadmap(
    evaluations: list[EvaluatedRequirement],
    recommendations: list[Recommendation],
    costs: list[CostItem],
    current_score: Decimal,
) -> list[RoadmapDraft]:
    drafts = rank_recommendations(map_gaps_to_recommendations(evaluations, recommendations, costs))
    already_covered: set[str] = set()
    for draft in drafts:
        draft.gain = calculate_recommendation_gain(draft, already_covered)
    projections = project_score_after_actions(current_score, [item.gain for item in drafts])
    for draft, projection in zip(drafts, projections, strict=True):
        draft.projected_score = projection
    return drafts
