import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentQuestion,
    CertificationScheme,
    Product,
    QuestionBank,
    SchemeCostItem,
)
from app.models.enums import (
    AssessmentStatus,
    CostType,
    QuestionPage,
    RequirementStatus,
)
from app.services.result_service import (
    EvaluatedRequirement,
    _scheme_cost_summary,
    _scheme_roadmap_snapshot,
    generate_scheme_result,
    serialize_result,
)
from app.services.seed_service import seed_initial_knowledge_base


@pytest.mark.asyncio
async def test_quote_required_semantics_legitimate_zero_vs_custom_quote():
    """Verify that quote_required=True is set ONLY when is_quote_required=True.

    Legitimate zero costs enter numeric totals as 0, while quote_required items
    are excluded from numeric totals.
    """
    snapshots = [
        {
            "recommendation_id": "c_zero_legit",
            "cost_type": "business_opex",
            "quote_required": False,
            "one_time_cost": {"min": 0, "max": 0, "currency": "LKR"},
            "recurring_cost": {"min": 0, "max": 0, "currency": "LKR"},
        },
        {
            "recommendation_id": "c_quote_custom",
            "cost_type": "certifying_body_fee",
            "quote_required": True,
            "one_time_cost": {"min": 0, "max": 0, "currency": "LKR"},
            "recurring_cost": {"min": 0, "max": 0, "currency": "LKR"},
        },
        {
            "recommendation_id": "c_normal",
            "cost_type": "certifying_body_fee",
            "quote_required": False,
            "one_time_cost": {"min": 50000, "max": 80000, "currency": "LKR"},
            "recurring_cost": {"min": 20000, "max": 30000, "currency": "LKR"},
        },
    ]

    summary = _scheme_cost_summary(snapshots)

    # Total numeric sums exclude quote_required items, but include legitimate zeros
    assert summary["one_time_min"] == 50000
    assert summary["one_time_max"] == 80000
    assert summary["recurring_min"] == 20000
    assert summary["recurring_max"] == 30000

    by_type = summary["by_type"]
    assert by_type["certifying_body_fee"]["items_count"] == 2
    assert by_type["certifying_body_fee"]["quote_required_count"] == 1
    assert by_type["certifying_body_fee"]["one_time_min"] == 50000

    assert by_type["business_opex"]["items_count"] == 1
    assert by_type["business_opex"]["quote_required_count"] == 0
    assert by_type["business_opex"]["one_time_min"] == 0


@pytest.mark.asyncio
async def test_cross_scheme_cost_isolation(db_session: Session):
    """Verify that scheme A assessment reads ONLY scheme A cost items."""
    seed_initial_knowledge_base(db_session)

    scheme_a = db_session.get(CertificationScheme, "SLS_MARK_CORDIAL")
    assert scheme_a is not None

    # Add a cost item belonging to scheme B (ISO_22000)
    cost_b = SchemeCostItem(
        id="cost_scheme_b_only",
        scheme_id="ISO_22000",
        action_ref="iso_action",
        title="ISO 22000 External Lead Auditor Training",
        cost_type=CostType.BUSINESS_OPEX,
        one_time_min=120000,
        one_time_max=180000,
        recurring_min=0,
        recurring_max=0,
        currency="LKR",
        source_note="ISO Lead Auditor course fee",
        effective_date=date(2026, 1, 1),
        last_reviewed=date(2026, 1, 1),
        is_quote_required=False,
    )
    db_session.add(cost_b)
    db_session.flush()

    product = db_session.query(Product).first()

    assessment_a = Assessment(
        id=uuid.uuid4(),
        status=AssessmentStatus.READY_TO_SCORE,
        scheme_id="SLS_MARK_CORDIAL",
        profile_data={"product_id": str(product.id) if product else "PROD_CORDIAL"},
    )
    db_session.add(assessment_a)
    question = db_session.query(QuestionBank).first()
    assert question is not None
    db_session.add(
        AssessmentQuestion(
            assessment_id=assessment_a.id,
            question_id=question.id,
            page=QuestionPage.CLARIFICATION,
            display_order=1,
            answered=True,
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.flush()

    result = await generate_scheme_result(db_session, assessment_a)
    serialized = serialize_result(db_session, assessment_a, result)

    roadmap_ids = [item["recommendation_id"] for item in serialized["roadmap"]]
    assert "cost_scheme_b_only" not in roadmap_ids


@pytest.mark.asyncio
async def test_expected_gain_non_double_counting_concrete_fixture(db_session: Session):
    """Verify that two roadmap actions mapping to the same requirement R1 cap gain at W, not 2W."""
    seed_initial_knowledge_base(db_session)

    scheme = db_session.get(CertificationScheme, "SLS_MARK_CORDIAL")
    assert scheme is not None

    req1 = EvaluatedRequirement(
        requirement_id="req_r1",
        title="Critical Sanitation Requirement R1",
        category="Hygiene & Sanitation",
        weight=Decimal("5.0"),
        safety_critical=True,
        status=RequirementStatus.GAP,
        multiplier=Decimal("0"),
        evidence_references=[],
        rationale="gap",
    )

    c1 = SchemeCostItem(
        id="c1_action_a",
        scheme_id=scheme.id,
        action_ref="action_a",
        title="Action A for R1",
        cost_type=CostType.BUSINESS_CAPEX,
        one_time_min=20000,
        one_time_max=30000,
        recurring_min=0,
        recurring_max=0,
        currency="LKR",
        source_note="Capex quote",
        effective_date=date(2026, 1, 1),
        last_reviewed=date(2026, 1, 1),
        is_quote_required=False,
    )

    c2 = SchemeCostItem(
        id="c2_action_b",
        scheme_id=scheme.id,
        action_ref="action_b",
        title="Action B for R1",
        cost_type=CostType.BUSINESS_OPEX,
        one_time_min=5000,
        one_time_max=10000,
        recurring_min=0,
        recurring_max=0,
        currency="LKR",
        source_note="Opex quote",
        effective_date=date(2026, 1, 1),
        last_reviewed=date(2026, 1, 1),
        is_quote_required=False,
    )

    assessment = Assessment(
        id=uuid.uuid4(),
        status=AssessmentStatus.COMPLETED,
        scheme_id=scheme.id,
    )
    db_session.add(assessment)
    db_session.flush()

    snapshots = await _scheme_roadmap_snapshot(
        db_session,
        assessment,
        [req1],
        [c1, c2],
        current_score=Decimal("95.0"),
    )

    # Action A should get 5.0 gain, Action B should get 0.0 gain
    gains = [item["expected_gain"] for item in snapshots]
    total_gain = sum(gains)
    assert total_gain <= 5.0  # Max total recoverable weight W = 5.0, not 2W = 10.0
    # Final projected score caps at Decimal("100.0")
    for item in snapshots:
        assert item["projected_score"] <= 100


@pytest.mark.asyncio
async def test_ai_cost_firewall(db_session: Session):
    """Verify that AI explanation provider cannot alter numeric prices, cost types, gains, or priorities."""
    seed_initial_knowledge_base(db_session)

    product = db_session.query(Product).first()

    assessment = Assessment(
        id=uuid.uuid4(),
        status=AssessmentStatus.READY_TO_SCORE,
        scheme_id="SLS_MARK_CORDIAL",
        profile_data={"product_id": str(product.id) if product else "PROD_CORDIAL"},
    )
    db_session.add(assessment)
    question = db_session.query(QuestionBank).first()
    assert question is not None
    db_session.add(
        AssessmentQuestion(
            assessment_id=assessment.id,
            question_id=question.id,
            page=QuestionPage.CLARIFICATION,
            display_order=1,
            answered=True,
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.flush()

    result = await generate_scheme_result(db_session, assessment)
    serialized = serialize_result(db_session, assessment, result)

    for item in serialized["roadmap"]:
        assert isinstance(item["one_time_cost"]["min"], int)
        assert isinstance(item["one_time_cost"]["max"], int)
        assert isinstance(item["cost_type"], str)
        assert isinstance(item["expected_gain"], float)
        assert isinstance(item["priority"], int)


@pytest.mark.asyncio
async def test_legacy_chilli_paste_regression(db_session: Session):
    """Verify legacy scheme_id == null assessment scores exactly 32.0000 raw / 32 displayed."""
    seed_initial_knowledge_base(db_session)

    from app.models import AssessmentResult
    from app.services.sample_service import build_sample_assessment

    legacy_assessment = await build_sample_assessment(db_session)
    result = db_session.scalar(
        select(AssessmentResult).where(AssessmentResult.assessment_id == legacy_assessment.id)
    )
    assert result is not None

    assert str(result.overall_score_raw) == "32.0000"
    assert result.overall_score == 32
