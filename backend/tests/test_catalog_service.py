from sqlalchemy.orm import Session

from app.models.enums import CertificationTrack
from app.services.catalog_service import (
    get_scheme,
    get_scheme_cost_items,
    get_scheme_requirements,
    has_unverified_requirements,
    list_categories,
    list_products,
    list_schemes,
    list_schemes_for_product,
)


def test_list_categories_and_products(db: Session) -> None:
    cats = list_categories(db)
    assert len(cats) >= 1
    food_cat = cats[0]
    assert food_cat.name == "Food Products"
    assert food_cat.slug == "food_products"

    prods = list_products(db, str(food_cat.id))
    assert len(prods) >= 1
    cordial = prods[0]
    assert cordial.name == "Fresh Fruit Cordial"
    assert cordial.slug == "fresh_fruit_cordial"


def test_list_schemes(db: Session) -> None:
    schemes = list_schemes(db)
    assert len(schemes) >= 2  # SLS Mark + CAA

    product_quality_schemes = list_schemes(db, track=CertificationTrack.PRODUCT_QUALITY)
    assert any(s.id == "SLS_MARK_CORDIAL" for s in product_quality_schemes)
    assert any(s.id == "CAA_FOOD_REG" for s in product_quality_schemes)

    scheme = get_scheme(db, "SLS_MARK_CORDIAL")
    assert scheme is not None
    assert scheme.name == "SLS Mark — Fresh Fruit Cordial"
    assert scheme.body.id == "SLSI"


def test_scheme_requirements_and_costs(db: Session) -> None:
    reqs = get_scheme_requirements(db, "SLS_MARK_CORDIAL")
    assert len(reqs) == 21
    assert any(r.id == "SLS_HYG_HANDWASH" for r in reqs)

    costs = get_scheme_cost_items(db, "SLS_MARK_CORDIAL")
    assert len(costs) == 8

    assert has_unverified_requirements(db, "SLS_MARK_CORDIAL") is True


def test_list_schemes_for_product(db: Session) -> None:
    cats = list_categories(db)
    prods = list_products(db, str(cats[0].id))
    cordial_id = str(prods[0].id)

    schemes = list_schemes_for_product(db, cordial_id)
    assert len(schemes) >= 2
    assert any(s.id == "SLS_MARK_CORDIAL" for s in schemes)


# ── Track 2 — Process Management ─────────────────────────────────────────────

def test_track2_schemes_seeded(db: Session) -> None:
    """Track 2 schemes GMP, HACCP, ISO 22000 must all be seeded and active."""
    pm_schemes = list_schemes(db, track=CertificationTrack.PROCESS_MANAGEMENT)
    scheme_ids = {s.id for s in pm_schemes}
    assert "SLS_GMP" in scheme_ids, "SLS_GMP scheme not seeded"
    assert "SLS_HACCP" in scheme_ids, "SLS_HACCP scheme not seeded"
    assert "ISO_22000" in scheme_ids, "ISO_22000 scheme not seeded"

    # Track 2 schemes must not appear in Track 1 filter
    pq_schemes = list_schemes(db, track=CertificationTrack.PRODUCT_QUALITY)
    pq_ids = {s.id for s in pq_schemes}
    assert "SLS_GMP" not in pq_ids
    assert "SLS_HACCP" not in pq_ids
    assert "ISO_22000" not in pq_ids


def test_gmp_requirements_and_costs(db: Session) -> None:
    """GMP scheme must have exactly 18 requirements and 5 cost items."""
    reqs = get_scheme_requirements(db, "SLS_GMP")
    assert len(reqs) == 18, f"Expected 18 GMP requirements, got {len(reqs)}"
    assert any(r.id == "GMP_WATER_POTABLE" for r in reqs)
    assert any(r.safety_critical for r in reqs)

    costs = get_scheme_cost_items(db, "SLS_GMP")
    assert len(costs) == 5, f"Expected 5 GMP cost items, got {len(costs)}"
    assert has_unverified_requirements(db, "SLS_GMP") is True


def test_haccp_requirements_and_costs(db: Session) -> None:
    """HACCP scheme must have exactly 20 requirements and 6 cost items."""
    reqs = get_scheme_requirements(db, "SLS_HACCP")
    assert len(reqs) == 20, f"Expected 20 HACCP requirements, got {len(reqs)}"
    assert any(r.id == "HACCP_CL_DEFINED" for r in reqs)
    # Critical limits and biological hazard must be safety_critical
    assert any(r.id == "HACCP_CL_DEFINED" and r.safety_critical for r in reqs)

    costs = get_scheme_cost_items(db, "SLS_HACCP")
    assert len(costs) == 6, f"Expected 6 HACCP cost items, got {len(costs)}"
    assert has_unverified_requirements(db, "SLS_HACCP") is True


def test_iso22000_requirements_and_costs(db: Session) -> None:
    """ISO 22000 scheme must have exactly 22 requirements and 7 cost items."""
    reqs = get_scheme_requirements(db, "ISO_22000")
    assert len(reqs) == 22, f"Expected 22 ISO 22000 requirements, got {len(reqs)}"
    assert any(r.id == "ISO_HACCP_CCPS" for r in reqs)

    costs = get_scheme_cost_items(db, "ISO_22000")
    assert len(costs) == 7, f"Expected 7 ISO 22000 cost items, got {len(costs)}"
    assert has_unverified_requirements(db, "ISO_22000") is True
