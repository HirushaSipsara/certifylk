"""Add scheme linkage to evidence observations.

The certificate-specific ORM fields were omitted from revision 0004.  This
compatibility revision is conditional so it upgrades both fresh databases and
early deployments whose schema was created from current ORM metadata.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260807_0006"
down_revision = "20260807_0005"
branch_labels = None
depends_on = None


def _columns() -> set[str]:
    return {
        column["name"] for column in sa.inspect(op.get_bind()).get_columns("evidence_observations")
    }


def _has_foreign_key(name: str, columns: list[str], referred_table: str) -> bool:
    return any(
        (
            foreign_key.get("name") == name
            or (
                foreign_key.get("constrained_columns") == columns
                and foreign_key.get("referred_table") == referred_table
            )
        )
        for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys("evidence_observations")
    )


def _has_named_foreign_key(name: str) -> bool:
    return any(
        foreign_key.get("name") == name
        for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys("evidence_observations")
    )


def upgrade() -> None:
    columns = _columns()
    if "scheme_id" not in columns:
        op.add_column(
            "evidence_observations",
            sa.Column("scheme_id", sa.String(64), nullable=True),
        )
    if not _has_foreign_key(
        "fk_evidence_observations_scheme", ["scheme_id"], "certification_schemes"
    ):
        op.create_foreign_key(
            "fk_evidence_observations_scheme",
            "evidence_observations",
            "certification_schemes",
            ["scheme_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if "ix_evidence_observations_scheme_id" not in {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes("evidence_observations")
    }:
        op.create_index(
            "ix_evidence_observations_scheme_id",
            "evidence_observations",
            ["scheme_id"],
        )

    columns = _columns()
    if "scheme_requirement_id" not in columns:
        op.add_column(
            "evidence_observations",
            sa.Column("scheme_requirement_id", sa.String(64), nullable=True),
        )
    if not _has_foreign_key(
        "fk_evidence_observations_scheme_requirement",
        ["scheme_requirement_id"],
        "scheme_requirements",
    ):
        op.create_foreign_key(
            "fk_evidence_observations_scheme_requirement",
            "evidence_observations",
            "scheme_requirements",
            ["scheme_requirement_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if "ix_evidence_observations_scheme_requirement_id" not in {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes("evidence_observations")
    }:
        op.create_index(
            "ix_evidence_observations_scheme_requirement_id",
            "evidence_observations",
            ["scheme_requirement_id"],
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_named_foreign_key("fk_evidence_observations_scheme_requirement"):
        op.drop_constraint(
            "fk_evidence_observations_scheme_requirement",
            "evidence_observations",
            type_="foreignkey",
        )
    if "ix_evidence_observations_scheme_requirement_id" in {
        index["name"] for index in inspector.get_indexes("evidence_observations")
    }:
        op.drop_index(
            "ix_evidence_observations_scheme_requirement_id",
            table_name="evidence_observations",
        )
    if "scheme_requirement_id" in _columns():
        op.drop_column("evidence_observations", "scheme_requirement_id")

    if _has_named_foreign_key("fk_evidence_observations_scheme"):
        op.drop_constraint(
            "fk_evidence_observations_scheme",
            "evidence_observations",
            type_="foreignkey",
        )
    if "ix_evidence_observations_scheme_id" in {
        index["name"] for index in inspector.get_indexes("evidence_observations")
    }:
        op.drop_index("ix_evidence_observations_scheme_id", table_name="evidence_observations")
    if "scheme_id" in _columns():
        op.drop_column("evidence_observations", "scheme_id")
