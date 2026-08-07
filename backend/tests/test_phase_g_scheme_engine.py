import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    CertificationScheme,
    EvidenceExpectation,
    SchemeCostItem,
    SchemeRequirement,
)
from app.models.enums import AssessmentStatus, RequirementStatus
from app.services.result_service import (
    EvaluatedRequirement,
    _scheme_cost_summary,
    _scheme_priority,
    generate_scheme_result,
    serialize_result,
)
from app.services.seed_service import seed_initial_knowledge_base


@pytest.mark.asyncio
async def test_all_active_schemes_category_weights_sum_to_100(db_session: Session):
    """Verify category weights sum exactly to 100 for all active schemes."""
    seed_initial_knowledge_base(db_session)

    schemes = list(db_session.scalars(select_active_schemes()))
    assert len(schemes) >= 4

    for scheme in schemes:
        assert scheme.category_weights is not None
        total_weight = sum(Decimal(str(w)) for w in scheme.category_weights.values())
        assert total_weight == Decimal("100"), f"Scheme {scheme.id} category weights sum to {total_weight}, expected 100"


def select_active_schemes():
    from sqlalchemy import select
    return select(CertificationScheme).where(CertificationScheme.active == True)


@pytest.mark.asyncio
async def test_scheme_requirement_weights_sum_to_category_weight(db_session: Session):
    """Verify requirement weights within each category sum to that category's configured weight."""
    seed_initial_knowledge_base(db_session)

    schemes = list(db_session.scalars(select_active_schemes()))
    for scheme in schemes:
        reqs = list(
            db_session.scalars(
                select_requirements_by_scheme(scheme.id)
            )
        )
        by_category: dict[str, Decimal] = {}
        for req in reqs:
            cat = req.category_label
            by_category[cat] = by_category.get(cat, Decimal("0")) + req.weight

        for cat_name, cat_weight in scheme.category_weights.items():
            summed = by_category.get(cat_name, Decimal("0"))
            assert summed == Decimal(str(cat_weight)), (
                f"Scheme {scheme.id} category '{cat_name}' requirements sum to {summed}, expected {cat_weight}"
            )


def select_requirements_by_scheme(scheme_id: str):
    from sqlalchemy import select
    return select(SchemeRequirement).where(SchemeRequirement.scheme_id == scheme_id)


@pytest.mark.asyncio
async def test_not_applicable_excluded_from_denominator(db_session: Session):
    """Verify not_applicable requirement status excludes requirement weight from category denominator."""
    seed_initial_knowledge_base(db_session)

    req_active = EvaluatedRequirement(
        requirement_id="r1",
        title="Active Requirement",
        category_label="Hygiene & Sanitation",
        weight=Decimal("10.0"),
        safety_critical=False,
        status=RequirementStatus.CONFIRMED,
        multiplier=Decimal("1.0"),
    )
    req_na = EvaluatedRequirement(
        requirement_id="r2",
        title="NA Requirement",
        category_label="Hygiene & Sanitation",
        weight=Decimal("10.0"),
        safety_critical=False,
        status=RequirementStatus.NOT_APPLICABLE,
        multiplier=Decimal("0.0"),
    )

    # Hygiene & Sanitation category has 20 points configured
    # With req_na excluded from denominator, earned points (10/10) * 20 = 20 points
    evaluations = [req_active, req_na]
    from app.services.result_service import _evaluate_scheme_categories
    cat_weights = {"Hygiene & Sanitation": 20}
    cat_scores = _evaluate_scheme_categories(evaluations, cat_weights)

    hyg_score = next(c for c in cat_scores if c.category == "Hygiene & Sanitation")
    assert hyg_score.score == Decimal("20.0000")


@pytest.mark.asyncio
async def test_scheme_version_and_catalogue_revision_freezing(db_session: Session):
    """Verify completed result freezes scheme_version and catalogue_revision."""
    seed_initial_knowledge_base(db_session)

    assessment = Assessment(
        id="test-freeze-assessment",
        status=AssessmentStatus.READY_TO_SCORE,
        scheme_id="SLS_MARK_CORDIAL",
    )
    db_session.add(assessment)
    db_session.flush()

    result = await generate_scheme_result(db_session, assessment)
    assert result.scheme_version is not None
    assert result.catalogue_revision is not None
    assert result.scheme_version == "draft-2026-08"
    assert result.catalogue_revision == "2026-08-07-draft"


@pytest.mark.asyncio
async def test_content_verified_false_warning_flag(db_session: Session):
    """Verify content_verified remains false for current draft catalogue rows."""
    seed_initial_knowledge_base(db_session)

    reqs = list(db_session.scalars(select_requirements_by_scheme("SLS_MARK_CORDIAL")))
    assert len(reqs) > 0
    assert any(not r.content_verified for r in reqs)
