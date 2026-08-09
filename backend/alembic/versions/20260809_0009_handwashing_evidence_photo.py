"""Allow photo evidence for the SLS handwashing-facility requirement.

Revision ID: 20260809_0009
Revises: 20260809_0008
"""

import sqlalchemy as sa

from alembic import op

revision = "20260809_0009"
down_revision = "20260809_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text("UPDATE evidence_expectations SET kind = 'photo' WHERE id = 'EV_SLS_HYG_HANDWASH'")
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE evidence_expectations SET kind = 'document' WHERE id = 'EV_SLS_HYG_HANDWASH'"
        )
    )
