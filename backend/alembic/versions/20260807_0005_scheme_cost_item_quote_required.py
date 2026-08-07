"""Add is_quote_required to scheme_cost_items

Revision ID: 20260807_0005
Revises: 20260807_0004
Create Date: 2026-08-07 20:35:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "20260807_0005"
down_revision = "20260807_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("scheme_cost_items")}
    if "is_quote_required" not in columns:
        op.add_column(
            "scheme_cost_items",
            sa.Column("is_quote_required", sa.Boolean(), server_default="false", nullable=False),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("scheme_cost_items")}
    if "is_quote_required" in columns:
        op.drop_column("scheme_cost_items", "is_quote_required")
