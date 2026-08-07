"""Add certification knowledge base tables and extend assessments.

Revision ID: 20260807_0002
Revises: 20260805_0001
"""

import sqlalchemy as sa
from alembic import op

revision = "20260807_0002"
down_revision = "20260805_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = set(inspector.get_table_names())

    # ── business_profiles ────────────────────────────────────────────────────
    if "business_profiles" not in existing:
        op.create_table(
            "business_profiles",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("business_type", sa.String(40), nullable=False),
            sa.Column("years_operating", sa.Integer(), nullable=True),
            sa.Column("scale", sa.String(40), nullable=False),
            sa.Column("market", sa.JSON(), nullable=False),
            sa.Column("existing_certifications", sa.JSON(), nullable=False),
            sa.Column("has_food_licence", sa.String(20), nullable=False),
            sa.Column("monthly_volume_range", sa.String(40), nullable=True),
            sa.Column("additional_info", sa.String(2000), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # ── categories ───────────────────────────────────────────────────────────
    if "categories" not in existing:
        op.create_table(
            "categories",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("slug", sa.String(80), nullable=False),
            sa.Column("description", sa.String(500), nullable=False, server_default=""),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
            sa.UniqueConstraint("slug"),
        )
        op.create_index("ix_categories_slug", "categories", ["slug"])

    # ── products ─────────────────────────────────────────────────────────────
    if "products" not in existing:
        op.create_table(
            "products",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("category_id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("slug", sa.String(80), nullable=False),
            sa.Column("description", sa.String(500), nullable=False, server_default=""),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug"),
        )
        op.create_index("ix_products_category_id", "products", ["category_id"])
        op.create_index("ix_products_slug", "products", ["slug"])

    # ── certification_bodies ─────────────────────────────────────────────────
    if "certification_bodies" not in existing:
        op.create_table(
            "certification_bodies",
            sa.Column("id", sa.String(20), nullable=False),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("short_code", sa.String(20), nullable=False),
            sa.Column("website_url", sa.String(300), nullable=False, server_default=""),
            sa.Column("description", sa.String(500), nullable=False, server_default=""),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("short_code"),
        )

    # ── certification_schemes ────────────────────────────────────────────────
    if "certification_schemes" not in existing:
        op.create_table(
            "certification_schemes",
            sa.Column("id", sa.String(64), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("short_code", sa.String(30), nullable=False),
            sa.Column(
                "track",
                sa.Enum("product_quality", "process_management", name="certification_track", native_enum=False),
                nullable=False,
            ),
            sa.Column("body_id", sa.String(20), nullable=False),
            sa.Column("product_id", sa.Uuid(), nullable=True),
            sa.Column(
                "mandatory_tier",
                sa.Enum("mandatory", "market_required", "recommended", "optional", name="mandatory_tier", native_enum=False),
                nullable=False,
            ),
            sa.Column("applicability_rule", sa.JSON(), nullable=False),
            sa.Column("category_weights", sa.JSON(), nullable=False),
            sa.Column("summary", sa.String(500), nullable=False, server_default=""),
            sa.Column("typical_timeline_days", sa.Integer(), nullable=True),
            sa.Column("source_url", sa.String(300), nullable=False, server_default=""),
            sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["body_id"], ["certification_bodies.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_certification_schemes_track", "certification_schemes", ["track"])
        op.create_index("ix_certification_schemes_body_id", "certification_schemes", ["body_id"])
        op.create_index("ix_certification_schemes_product_id", "certification_schemes", ["product_id"])

    # ── scheme_requirements ──────────────────────────────────────────────────
    if "scheme_requirements" not in existing:
        op.create_table(
            "scheme_requirements",
            sa.Column("id", sa.String(64), nullable=False),
            sa.Column("scheme_id", sa.String(64), nullable=False),
            sa.Column("category_label", sa.String(80), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("weight", sa.Numeric(6, 3), nullable=False),
            sa.Column("safety_critical", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("source_document", sa.String(200), nullable=False, server_default=""),
            sa.Column("clause_reference", sa.String(100), nullable=False, server_default=""),
            sa.Column("source_url", sa.String(300), nullable=False, server_default=""),
            sa.Column("content_verified", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("evaluation_rule", sa.JSON(), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(["scheme_id"], ["certification_schemes.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_scheme_req_scheme_order", "scheme_requirements", ["scheme_id", "display_order"])
        op.create_index("ix_scheme_requirements_category_label", "scheme_requirements", ["category_label"])

    # ── scheme_cost_items ────────────────────────────────────────────────────
    if "scheme_cost_items" not in existing:
        op.create_table(
            "scheme_cost_items",
            sa.Column("id", sa.String(64), nullable=False),
            sa.Column("scheme_id", sa.String(64), nullable=False),
            sa.Column("action_ref", sa.String(64), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column(
                "cost_type",
                sa.Enum(
                    "certifying_body_fee", "lab_testing_fee", "business_capex", "business_opex",
                    name="cost_type", native_enum=False
                ),
                nullable=False,
            ),
            sa.Column("one_time_min", sa.Integer(), nullable=False),
            sa.Column("one_time_max", sa.Integer(), nullable=False),
            sa.Column("recurring_min", sa.Integer(), nullable=False),
            sa.Column("recurring_max", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False, server_default="LKR"),
            sa.Column("source_note", sa.String(500), nullable=False, server_default=""),
            sa.Column("effective_date", sa.Date(), nullable=False),
            sa.Column("last_reviewed", sa.Date(), nullable=False),
            sa.ForeignKeyConstraint(["scheme_id"], ["certification_schemes.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_scheme_cost_items_scheme_id", "scheme_cost_items", ["scheme_id"])

    # ── extend assessments with new nullable FKs ─────────────────────────────
    columns = {col["name"] for col in inspector.get_columns("assessments")}
    if "business_profile_id" not in columns:
        op.add_column(
            "assessments",
            sa.Column("business_profile_id", sa.Uuid(), nullable=True),
        )
        op.create_foreign_key(
            "fk_assessments_business_profile",
            "assessments", "business_profiles",
            ["business_profile_id"], ["id"],
            ondelete="SET NULL",
        )
        op.create_index("ix_assessments_business_profile_id", "assessments", ["business_profile_id"])

    if "scheme_id" not in columns:
        op.add_column(
            "assessments",
            sa.Column("scheme_id", sa.String(64), nullable=True),
        )
        op.create_foreign_key(
            "fk_assessments_scheme",
            "assessments", "certification_schemes",
            ["scheme_id"], ["id"],
            ondelete="SET NULL",
        )
        op.create_index("ix_assessments_scheme_id", "assessments", ["scheme_id"])

    if "product_id" not in columns:
        op.add_column(
            "assessments",
            sa.Column("product_id", sa.Uuid(), nullable=True),
        )
        op.create_foreign_key(
            "fk_assessments_product",
            "assessments", "products",
            ["product_id"], ["id"],
            ondelete="SET NULL",
        )
        op.create_index("ix_assessments_product_id", "assessments", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_assessments_product_id", table_name="assessments")
    op.drop_constraint("fk_assessments_product", "assessments", type_="foreignkey")
    op.drop_column("assessments", "product_id")

    op.drop_index("ix_assessments_scheme_id", table_name="assessments")
    op.drop_constraint("fk_assessments_scheme", "assessments", type_="foreignkey")
    op.drop_column("assessments", "scheme_id")

    op.drop_index("ix_assessments_business_profile_id", table_name="assessments")
    op.drop_constraint("fk_assessments_business_profile", "assessments", type_="foreignkey")
    op.drop_column("assessments", "business_profile_id")

    op.drop_table("scheme_cost_items")
    op.drop_table("scheme_requirements")
    op.drop_table("certification_schemes")
    op.drop_table("certification_bodies")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("business_profiles")
