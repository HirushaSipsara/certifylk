"""Allow certificate-specific IDs in evidence observations.

``evidence_observations.requirement_id`` was historically constrained to the
legacy ``requirements`` catalogue. Certificate-specific evidence uses a
``scheme_requirements`` ID in that displayed/reference field and retains a
separate foreign key in ``scheme_requirement_id``. Remove the obsolete legacy
foreign key so both supported assessment types can persist observations.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260807_0007"
down_revision = "20260807_0006"
branch_labels = None
depends_on = None


def _legacy_requirement_foreign_keys() -> list[str]:
    return [
        foreign_key["name"]
        for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys("evidence_observations")
        if foreign_key.get("constrained_columns") == ["requirement_id"]
        and foreign_key.get("referred_table") == "requirements"
        and foreign_key.get("name")
    ]


def upgrade() -> None:
    for constraint_name in _legacy_requirement_foreign_keys():
        op.drop_constraint(constraint_name, "evidence_observations", type_="foreignkey")


def downgrade() -> None:
    # A downgrade is only safe when no certificate-specific IDs are present.
    unmatched = op.get_bind().execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM evidence_observations observation
                LEFT JOIN requirements requirement ON requirement.id = observation.requirement_id
                WHERE requirement.id IS NULL
            )
            """
        )
    ).scalar_one()
    if unmatched:
        raise RuntimeError(
            "Cannot restore the legacy requirement foreign key while certificate-specific "
            "evidence observations exist."
        )
    op.create_foreign_key(
        "fk_evidence_observations_requirement_id_requirements",
        "evidence_observations",
        "requirements",
        ["requirement_id"],
        ["id"],
    )
