"""Add scheme_id and scheme_requirement_id to EvidenceObservation

Revision ID: 20260807_0006
Revises: 20260807_0005
Create Date: 2026-08-07 20:35:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "20260807_0006"
down_revision = "20260807_0005"
branch_labels = None
depends_on = None

def _columns(table_name: str) -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table_name)}

def upgrade() -> None:
    eval_columns = _columns("evidence_observations")
    if "scheme_id" not in eval_columns:
        op.add_column("evidence_observations", sa.Column("scheme_id", sa.String(64), nullable=True))
        op.create_index("ix_evidence_observations_scheme_id", "evidence_observations", ["scheme_id"])
        op.create_foreign_key(
            "fk_evidence_observations_scheme",
            "evidence_observations",
            "certification_schemes",
            ["scheme_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if "scheme_requirement_id" not in eval_columns:
        op.add_column(
            "evidence_observations",
            sa.Column("scheme_requirement_id", sa.String(64), nullable=True),
        )
        op.create_index(
            "ix_evidence_observations_scheme_requirement_id",
            "evidence_observations",
            ["scheme_requirement_id"],
        )
        op.create_foreign_key(
            "fk_evidence_observations_scheme_requirement",
            "evidence_observations",
            "scheme_requirements",
            ["scheme_requirement_id"],
            ["id"],
            ondelete="SET NULL",
        )

def downgrade() -> None:
    op.drop_constraint("fk_evidence_observations_scheme_requirement", "evidence_observations", type_="foreignkey")
    op.drop_index("ix_evidence_observations_scheme_requirement_id", table_name="evidence_observations")
    op.drop_column("evidence_observations", "scheme_requirement_id")
    op.drop_constraint("fk_evidence_observations_scheme", "evidence_observations", type_="foreignkey")
    op.drop_index("ix_evidence_observations_scheme_id", table_name="evidence_observations")
    op.drop_column("evidence_observations", "scheme_id")
