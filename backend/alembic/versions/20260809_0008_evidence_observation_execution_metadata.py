"""Persist exact execution metadata for each evidence observation.

Revision ID: 20260809_0008
Revises: 20260807_0007
"""

import sqlalchemy as sa

from alembic import op

revision = "20260809_0008"
down_revision = "20260807_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evidence_observations",
        sa.Column(
            "fallback_used",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "evidence_observations",
        sa.Column(
            "validation_status",
            sa.String(length=30),
            nullable=False,
            server_default="validated",
        ),
    )


def downgrade() -> None:
    op.drop_column("evidence_observations", "validation_status")
    op.drop_column("evidence_observations", "fallback_used")
