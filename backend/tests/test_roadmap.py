from datetime import date
from decimal import Decimal

from app.models import CostItem, Recommendation
from app.models.enums import RequirementStatus
from app.services.requirement_engine import EvaluatedRequirement
from app.services.roadmap_engine import build_roadmap


def test_roadmap_ranking_and_gain_are_deterministic() -> None:
    evaluation = EvaluatedRequirement(
        requirement_id="DOC_BATCH",
        category="documentation_records",
        title="Batch record",
        weight=Decimal("6"),
        safety_critical=False,
        status=RequirementStatus.GAP,
        multiplier=Decimal("0"),
        evidence_references=["answer.DOC_BATCH_01"],
        rationale="missing",
    )
    reviewed = date(2026, 8, 1)
    recommendation = Recommendation(
        id="REC_BATCH",
        title="Create record",
        implementation_steps=["Create template"],
        requirement_ids=["DOC_BATCH"],
        priority_base=10,
        is_capex=False,
        cost_note="catalogue",
        last_reviewed=reviewed,
        active=True,
    )
    cost = CostItem(
        id="COST_REC_BATCH",
        recommendation_id="REC_BATCH",
        one_time_min=0,
        one_time_max=1000,
        recurring_min=0,
        recurring_max=100,
        currency="LKR",
        effective_date=reviewed,
        last_reviewed=reviewed,
    )
    first = build_roadmap([evaluation], [recommendation], [cost], Decimal("40"))
    second = build_roadmap([evaluation], [recommendation], [cost], Decimal("40"))
    assert [(item.recommendation.id, item.gain) for item in first] == [
        (item.recommendation.id, item.gain) for item in second
    ]
    assert first[0].gain == Decimal("6.000")
    assert first[0].cost.one_time_max == 1000
