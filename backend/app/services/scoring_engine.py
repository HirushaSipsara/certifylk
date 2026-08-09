from decimal import ROUND_HALF_UP, Decimal

from app.data.catalog import CATEGORY_LABELS, CATEGORY_WEIGHTS
from app.models.enums import RequirementStatus
from app.services.requirement_engine import EvaluatedRequirement


def display_round(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_category_scores(
    evaluations: list[EvaluatedRequirement],
    category_weights: dict[str, int] | None = None,
) -> list[dict[str, object]]:
    weights = category_weights if category_weights is not None else CATEGORY_WEIGHTS
    labels = {k: CATEGORY_LABELS.get(k, k) for k in weights}
    scores: list[dict[str, object]] = []
    for category, category_weight in weights.items():
        category_items = [item for item in evaluations if item.category == category]
        applicable = [
            item for item in category_items if item.status != RequirementStatus.NOT_APPLICABLE
        ]
        denominator = sum((item.weight for item in applicable), Decimal("0"))
        if denominator == 0:
            continue
        earned = sum((item.weight * item.multiplier for item in applicable), Decimal("0"))
        normalized_points = (earned / denominator) * Decimal(category_weight)
        percentage = (earned / denominator) * Decimal("100")
        scores.append(
            {
                "category": category,
                "label": labels.get(category, category),
                "score_raw": normalized_points.quantize(Decimal("0.0001")),
                "score": display_round(percentage),
                "weight": category_weight,
            }
        )
    return scores


def calculate_readiness_score(category_scores: list[dict[str, object]]) -> Decimal:
    if not category_scores:
        return Decimal("0.0000")
    earned = sum((Decimal(str(score["score_raw"])) for score in category_scores), Decimal("0"))
    possible = sum((Decimal(str(score["weight"])) for score in category_scores), Decimal("0"))
    if possible == 0:
        return Decimal("0.0000")
    return ((earned / possible) * Decimal("100")).quantize(Decimal("0.0001"))


def calculate_evidence_completeness(evaluations: list[EvaluatedRequirement]) -> int:
    applicable = [item for item in evaluations if item.status != RequirementStatus.NOT_APPLICABLE]
    if not applicable:
        return 0
    evidenced = sum(
        item.status in {RequirementStatus.CONFIRMED, RequirementStatus.PARTIAL}
        and any(reference.startswith("evidence:") for reference in item.evidence_references)
        for item in applicable
    )
    return display_round(Decimal(evidenced) / Decimal(len(applicable)) * Decimal("100"))


def project_score_after_actions(current_score: Decimal, gains: list[Decimal]) -> list[Decimal]:
    projections: list[Decimal] = []
    projected = current_score
    for gain in gains:
        projected = min(Decimal("100"), projected + gain)
        projections.append(projected.quantize(Decimal("0.0001")))
    return projections
