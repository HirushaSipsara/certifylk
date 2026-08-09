"""Persist requirement-specific evidence-stage self-assessment.

Revision ID: 20260809_0011
Revises: 20260809_0010
"""

import sqlalchemy as sa

from alembic import op

revision = "20260809_0011"
down_revision = "20260809_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evidence_requests",
        sa.Column("self_assessment", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evidence_requests", "self_assessment")
