from decimal import Decimal

from app.data.catalog import CATEGORY_WEIGHTS, RECOMMENDATIONS, REQUIREMENTS
from app.models.enums import RequirementStatus
from app.services.requirement_engine import EvaluatedRequirement
from app.services.scoring_engine import (
    calculate_category_scores,
    calculate_evidence_completeness,
    calculate_readiness_score,
)


def evaluation(
    requirement_id: str,
    category: str,
    weight: int,
    status: RequirementStatus,
) -> EvaluatedRequirement:
    multiplier = {
        RequirementStatus.CONFIRMED: Decimal("1"),
        RequirementStatus.PARTIAL: Decimal("0.5"),
        RequirementStatus.GAP: Decimal("0"),
        RequirementStatus.UNKNOWN: Decimal("0"),
        RequirementStatus.NOT_APPLICABLE: Decimal("0"),
    }[status]
    return EvaluatedRequirement(
        requirement_id=requirement_id,
        category=category,
        title=requirement_id,
        weight=Decimal(weight),
        safety_critical=False,
        status=status,
        multiplier=multiplier,
        evidence_references=[],
        rationale="test",
    )


def test_category_and_requirement_weights_sum_correctly() -> None:
    assert sum(CATEGORY_WEIGHTS.values()) == 100
    for category, expected in CATEGORY_WEIGHTS.items():
        actual = sum(item["weight"] for item in REQUIREMENTS if item["category"] == category)
        assert actual == expected


def test_unknown_and_gap_are_distinct_but_score_zero() -> None:
    gap = evaluation("gap", "hygiene_sanitation", 10, RequirementStatus.GAP)
    unknown = evaluation("unknown", "hygiene_sanitation", 10, RequirementStatus.UNKNOWN)
    assert gap.status != unknown.status
    assert gap.multiplier == unknown.multiplier == 0
    scores = calculate_category_scores([gap, unknown])
    assert scores[0]["score_raw"] == Decimal("0.0000")


def test_not_applicable_is_safely_normalized() -> None:
    confirmed = evaluation("yes", "hygiene_sanitation", 5, RequirementStatus.CONFIRMED)
    excluded = evaluation("na", "hygiene_sanitation", 15, RequirementStatus.NOT_APPLICABLE)
    scores = calculate_category_scores([confirmed, excluded])
    assert scores[0]["score"] == 100
    assert calculate_readiness_score(scores) == Decimal("100.0000")
    assert calculate_evidence_completeness([confirmed, excluded]) == 100


def test_costs_exist_only_in_curated_catalogue() -> None:
    assert len(RECOMMENDATIONS) >= 12
    for item in RECOMMENDATIONS:
        assert item[7] >= item[6] >= 0
        assert item[9] >= item[8] >= 0
