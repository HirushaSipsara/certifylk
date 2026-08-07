"""Catalog service — read-only queries over the certification knowledge base."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    CertificationScheme,
    EvidenceExpectation,
    Product,
    SchemeCostItem,
    SchemeRequirement,
    SourceDocument,
)
from app.models.enums import CertificationTrack


def list_categories(db: Session) -> list[Category]:
    """Return all enabled categories ordered by display_order."""
    return list(
        db.scalars(
            select(Category)
            .where(Category.enabled.is_(True))
            .order_by(Category.display_order, Category.name)
        )
    )


def get_category(db: Session, category_id: str) -> Category | None:
    """Return a single category by UUID string or None."""
    import uuid as _uuid

    try:
        cid = _uuid.UUID(category_id)
    except ValueError:
        return None
    return db.get(Category, cid)


def list_products(db: Session, category_id: str) -> list[Product]:
    """Return all enabled products for a category ordered by display_order."""
    import uuid as _uuid

    try:
        cid = _uuid.UUID(category_id)
    except ValueError:
        return []
    return list(
        db.scalars(
            select(Product)
            .where(Product.category_id == cid, Product.enabled.is_(True))
            .order_by(Product.display_order, Product.name)
        )
    )


def get_product_by_slug(db: Session, slug: str) -> Product | None:
    """Return a product by its slug or None."""
    return db.scalar(select(Product).where(Product.slug == slug))


def list_schemes(
    db: Session,
    track: CertificationTrack | None = None,
    *,
    active_only: bool = True,
) -> list[CertificationScheme]:
    """Return certification schemes, optionally filtered by track."""
    stmt = select(CertificationScheme).order_by(
        CertificationScheme.display_order, CertificationScheme.name
    )
    if active_only:
        stmt = stmt.where(CertificationScheme.active.is_(True))
    if track is not None:
        stmt = stmt.where(CertificationScheme.track == track)
    return list(db.scalars(stmt))


def list_schemes_for_product(
    db: Session,
    product_id: str | None,
    track: CertificationTrack | None = None,
) -> list[CertificationScheme]:
    """Return all active schemes for a product (including product-agnostic ones)."""
    import uuid as _uuid

    stmt = select(CertificationScheme).where(CertificationScheme.active.is_(True))
    if track is not None:
        stmt = stmt.where(CertificationScheme.track == track)
    if product_id:
        try:
            pid = _uuid.UUID(product_id)
            stmt = stmt.where(
                (CertificationScheme.product_id == pid) | CertificationScheme.product_id.is_(None)
            )
        except ValueError:
            pass
    return list(db.scalars(stmt.order_by(CertificationScheme.display_order)))


def get_scheme(db: Session, scheme_id: str) -> CertificationScheme | None:
    """Return a scheme by ID or None."""
    return db.get(CertificationScheme, scheme_id)


def get_scheme_requirements(
    db: Session, scheme_id: str, *, active_only: bool = True
) -> list[SchemeRequirement]:
    """Return requirements for a scheme, ordered by display_order."""
    stmt = (
        select(SchemeRequirement)
        .where(SchemeRequirement.scheme_id == scheme_id)
        .order_by(SchemeRequirement.display_order)
    )
    if active_only:
        stmt = stmt.where(SchemeRequirement.active.is_(True))
    return list(db.scalars(stmt))


def get_scheme_cost_items(db: Session, scheme_id: str) -> list[SchemeCostItem]:
    """Return cost items for a scheme."""
    return list(
        db.scalars(
            select(SchemeCostItem)
            .where(SchemeCostItem.scheme_id == scheme_id)
            .order_by(SchemeCostItem.id)
        )
    )


def get_source_documents(db: Session) -> list[SourceDocument]:
    """Return source register rows ordered by owner and ID."""
    return list(
        db.scalars(select(SourceDocument).order_by(SourceDocument.owner_body_id, SourceDocument.id))
    )


def get_evidence_expectations(db: Session, scheme_id: str) -> list[EvidenceExpectation]:
    """Return active evidence expectations for a scheme."""
    return list(
        db.scalars(
            select(EvidenceExpectation)
            .where(EvidenceExpectation.scheme_id == scheme_id, EvidenceExpectation.active.is_(True))
            .order_by(EvidenceExpectation.display_order, EvidenceExpectation.id)
        )
    )


def has_unverified_requirements(db: Session, scheme_id: str) -> bool:
    """Return True if any active requirement for the scheme has content_verified=False."""
    reqs = get_scheme_requirements(db, scheme_id)
    return any(not r.content_verified for r in reqs)
