"""Add certificate-specific source, evidence, and result snapshot fields.

Revision ID: 20260807_0004
Revises: 20260807_0003
"""

import sqlalchemy as sa
from alembic import op

revision = "20260807_0004"
down_revision = "20260807_0003"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = set(inspector.get_table_names())

    if "source_documents" not in existing:
        op.create_table(
            "source_documents",
            sa.Column("id", sa.String(64), nullable=False),
            sa.Column("title", sa.String(250), nullable=False),
            sa.Column("owner_body_id", sa.String(20), nullable=False),
            sa.Column("version", sa.String(60), nullable=False, server_default=""),
            sa.Column("effective_date", sa.Date(), nullable=True),
            sa.Column("source_url", sa.String(300), nullable=False, server_default=""),
            sa.Column("access_reference", sa.String(300), nullable=False, server_default=""),
            sa.Column("copyright_note", sa.String(500), nullable=False, server_default=""),
            sa.Column("reviewer", sa.String(120), nullable=False, server_default=""),
            sa.Column("review_date", sa.Date(), nullable=True),
            sa.Column("content_verified", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("notes", sa.String(1000), nullable=False, server_default=""),
            sa.ForeignKeyConstraint(["owner_body_id"], ["certification_bodies.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_source_documents_owner_body_id", "source_documents", ["owner_body_id"])

    scheme_columns = _columns("certification_schemes")
    if "standard_version" not in scheme_columns:
        op.add_column(
            "certification_schemes",
            sa.Column("standard_version", sa.String(40), nullable=False, server_default="draft-2026-08"),
        )
    if "effective_date" not in scheme_columns:
        op.add_column("certification_schemes", sa.Column("effective_date", sa.Date(), nullable=True))
    if "source_document_id" not in scheme_columns:
        op.add_column(
            "certification_schemes",
            sa.Column("source_document_id", sa.String(64), nullable=True),
        )
        op.create_foreign_key(
            "fk_certification_schemes_source_document",
            "certification_schemes",
            "source_documents",
            ["source_document_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if "catalogue_revision" not in scheme_columns:
        op.add_column(
            "certification_schemes",
            sa.Column("catalogue_revision", sa.String(80), nullable=False, server_default="2026-08-07-draft"),
        )

    req_columns = _columns("scheme_requirements")
    if "source_document_id" not in req_columns:
        op.add_column(
            "scheme_requirements",
            sa.Column("source_document_id", sa.String(64), nullable=True),
        )
        op.create_foreign_key(
            "fk_scheme_requirements_source_document",
            "scheme_requirements",
            "source_documents",
            ["source_document_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if "standard_version" not in req_columns:
        op.add_column(
            "scheme_requirements",
            sa.Column("standard_version", sa.String(40), nullable=False, server_default="draft-2026-08"),
        )
    if "effective_date" not in req_columns:
        op.add_column("scheme_requirements", sa.Column("effective_date", sa.Date(), nullable=True))

    assessment_columns = _columns("assessments")
    if "scheme_version" not in assessment_columns:
        op.add_column("assessments", sa.Column("scheme_version", sa.String(40), nullable=True))
    if "catalogue_revision" not in assessment_columns:
        op.add_column("assessments", sa.Column("catalogue_revision", sa.String(80), nullable=True))

    for foreign_key in inspector.get_foreign_keys("requirement_evaluations"):
        if (
            foreign_key.get("referred_table") == "requirements"
            and foreign_key.get("constrained_columns") == ["requirement_id"]
            and foreign_key.get("name")
        ):
            op.drop_constraint(
                foreign_key["name"],
                "requirement_evaluations",
                type_="foreignkey",
            )
            break

    eval_columns = _columns("requirement_evaluations")
    if "scheme_id" not in eval_columns:
        op.add_column("requirement_evaluations", sa.Column("scheme_id", sa.String(64), nullable=True))
        op.create_index("ix_requirement_evaluations_scheme_id", "requirement_evaluations", ["scheme_id"])
        op.create_foreign_key(
            "fk_requirement_evaluations_scheme",
            "requirement_evaluations",
            "certification_schemes",
            ["scheme_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if "scheme_requirement_id" not in eval_columns:
        op.add_column(
            "requirement_evaluations",
            sa.Column("scheme_requirement_id", sa.String(64), nullable=True),
        )
        op.create_index(
            "ix_requirement_evaluations_scheme_requirement_id",
            "requirement_evaluations",
            ["scheme_requirement_id"],
        )
        op.create_foreign_key(
            "fk_requirement_evaluations_scheme_requirement",
            "requirement_evaluations",
            "scheme_requirements",
            ["scheme_requirement_id"],
            ["id"],
            ondelete="SET NULL",
        )

    result_columns = _columns("assessment_results")
    if "roadmap_snapshot" not in result_columns:
        op.add_column(
            "assessment_results",
            sa.Column("roadmap_snapshot", sa.JSON(), nullable=False, server_default="[]"),
        )
    if "scheme_id" not in result_columns:
        op.add_column("assessment_results", sa.Column("scheme_id", sa.String(64), nullable=True))
        op.create_index("ix_assessment_results_scheme_id", "assessment_results", ["scheme_id"])
    if "scheme_version" not in result_columns:
        op.add_column("assessment_results", sa.Column("scheme_version", sa.String(40), nullable=True))
    if "catalogue_revision" not in result_columns:
        op.add_column("assessment_results", sa.Column("catalogue_revision", sa.String(80), nullable=True))

    if "evidence_expectations" not in existing:
        op.create_table(
            "evidence_expectations",
            sa.Column("id", sa.String(80), nullable=False),
            sa.Column("scheme_id", sa.String(64), nullable=False),
            sa.Column("requirement_id", sa.String(64), nullable=False),
            sa.Column("kind", sa.String(30), nullable=False),
            sa.Column("label", sa.String(180), nullable=False),
            sa.Column("guidance_text", sa.String(700), nullable=False, server_default=""),
            sa.Column("required", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(["scheme_id"], ["certification_schemes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["requirement_id"], ["scheme_requirements.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_evidence_expectations_scheme_id", "evidence_expectations", ["scheme_id"])
        op.create_index("ix_evidence_expectations_requirement_id", "evidence_expectations", ["requirement_id"])
        op.create_index(
            "ix_evidence_expectation_scheme_requirement",
            "evidence_expectations",
            ["scheme_id", "requirement_id"],
        )


def downgrade() -> None:
    op.drop_index("ix_evidence_expectation_scheme_requirement", table_name="evidence_expectations")
    op.drop_index("ix_evidence_expectations_requirement_id", table_name="evidence_expectations")
    op.drop_index("ix_evidence_expectations_scheme_id", table_name="evidence_expectations")
    op.drop_table("evidence_expectations")

    op.drop_column("assessment_results", "catalogue_revision")
    op.drop_column("assessment_results", "scheme_version")
    op.drop_index("ix_assessment_results_scheme_id", table_name="assessment_results")
    op.drop_column("assessment_results", "scheme_id")
    op.drop_column("assessment_results", "roadmap_snapshot")

    op.drop_constraint("fk_requirement_evaluations_scheme_requirement", "requirement_evaluations", type_="foreignkey")
    op.drop_index("ix_requirement_evaluations_scheme_requirement_id", table_name="requirement_evaluations")
    op.drop_column("requirement_evaluations", "scheme_requirement_id")
    op.drop_constraint("fk_requirement_evaluations_scheme", "requirement_evaluations", type_="foreignkey")
    op.drop_index("ix_requirement_evaluations_scheme_id", table_name="requirement_evaluations")
    op.drop_column("requirement_evaluations", "scheme_id")

    op.drop_column("assessments", "catalogue_revision")
    op.drop_column("assessments", "scheme_version")
    op.drop_column("scheme_requirements", "effective_date")
    op.drop_column("scheme_requirements", "standard_version")
    op.drop_constraint("fk_scheme_requirements_source_document", "scheme_requirements", type_="foreignkey")
    op.drop_column("scheme_requirements", "source_document_id")
    op.drop_column("certification_schemes", "catalogue_revision")
    op.drop_constraint("fk_certification_schemes_source_document", "certification_schemes", type_="foreignkey")
    op.drop_column("certification_schemes", "source_document_id")
    op.drop_column("certification_schemes", "effective_date")
    op.drop_column("certification_schemes", "standard_version")
    op.drop_index("ix_source_documents_owner_body_id", table_name="source_documents")
    op.drop_table("source_documents")
