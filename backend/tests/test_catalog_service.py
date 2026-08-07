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
