"""Create the complete Phase 1 schema.

Revision ID: 20260805_0001
Revises: None
"""

from alembic import op

from app.db.base import Base
from app.models import *  # noqa: F403

revision = "20260805_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

