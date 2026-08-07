"""Create the complete Phase 1 schema.

Revision ID: 20260805_0001
Revises: None
"""

from alembic import op
import sqlalchemy as sa

revision = "20260805_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("current_page", sa.String(30), nullable=False),
        sa.Column("is_sample", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("profile_data", sa.JSON(), nullable=False),
        sa.Column("process_analysis", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessments_status", "assessments", ["status"])
    op.create_index("ix_assessments_status_created", "assessments", ["status", "created_at"])

    op.create_table(
        "assessment_answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("page", sa.String(32), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "page", "key", name="uq_answer_assessment_page_key"),
    )
    op.create_index("ix_answers_assessment_created", "assessment_answers", ["assessment_id", "created_at"])
    op.create_index("ix_assessment_answers_assessment_id", "assessment_answers", ["assessment_id"])
    op.create_index("ix_assessment_answers_key", "assessment_answers", ["key"])

    op.create_table(
        "process_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("normalized_name", sa.String(200), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "position", name="uq_step_assessment_position"),
    )
    op.create_index("ix_process_steps_assessment_id", "process_steps", ["assessment_id"])

    op.create_table(
        "question_bank",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("allows_other", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("product_tags", sa.JSON(), nullable=False),
        sa.Column("process_tags", sa.JSON(), nullable=False),
        sa.Column("requirement_ids", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("page_eligibility", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_question_bank_category", "question_bank", ["category"])

    op.create_table(
        "assessment_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.String(64), nullable=False),
        sa.Column("page", sa.String(40), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("planning_rationale", sa.String(500), nullable=False, server_default=""),
        sa.Column("answered", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["question_bank.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "question_id", "page", name="uq_assessment_question_page"),
    )
    op.create_index("ix_assessment_questions_assessment_id", "assessment_questions", ["assessment_id"])
    op.create_index("ix_assessment_questions_question_id", "assessment_questions", ["question_id"])

    op.create_table(
        "evidence_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("requirement_ids", sa.JSON(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(40), nullable=False, server_default="requested"),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "evidence_type", name="uq_evidence_request_assessment_type"),
    )
    op.create_index("ix_evidence_request_assessment_status", "evidence_requests", ["assessment_id", "status"])
    op.create_index("ix_evidence_requests_assessment_id", "evidence_requests", ["assessment_id"])
    op.create_index("ix_evidence_requests_status", "evidence_requests", ["status"])

    op.create_table(
        "evidence_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_request_id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(300), nullable=False),
        sa.Column("original_name", sa.String(200), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_request_id"], ["evidence_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_request_id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_evidence_files_assessment_id", "evidence_files", ["assessment_id"])
    op.create_index("ix_evidence_files_evidence_request_id", "evidence_files", ["evidence_request_id"])

    op.create_table(
        "evidence_observations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_request_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_file_id", sa.Uuid(), nullable=True),
        sa.Column("requirement_id", sa.String(64), nullable=False),
        sa.Column("polarity", sa.String(30), nullable=False),
        sa.Column("text", sa.String(1000), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_file_id"], ["evidence_files.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evidence_request_id"], ["evidence_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_observations_assessment_id", "evidence_observations", ["assessment_id"])
    op.create_index("ix_evidence_observations_evidence_file_id", "evidence_observations", ["evidence_file_id"])
    op.create_index("ix_evidence_observations_evidence_request_id", "evidence_observations", ["evidence_request_id"])
    op.create_index("ix_evidence_observations_requirement_id", "evidence_observations", ["requirement_id"])
    op.create_index("ix_observation_assessment_created", "evidence_observations", ["assessment_id", "created_at"])

    op.create_table(
        "requirements",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("weight", sa.Numeric(6, 3), nullable=False),
        sa.Column("safety_critical", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("applicability_tags", sa.JSON(), nullable=False),
        sa.Column("evaluation_rule", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_requirements_category", "requirements", ["category"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("implementation_steps", sa.JSON(), nullable=False),
        sa.Column("requirement_ids", sa.JSON(), nullable=False),
        sa.Column("priority_base", sa.Integer(), nullable=False),
        sa.Column("is_capex", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("cost_note", sa.String(500), nullable=False),
        sa.Column("last_reviewed", sa.Date(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "cost_items",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("recommendation_id", sa.String(64), nullable=False),
        sa.Column("one_time_min", sa.Integer(), nullable=False),
        sa.Column("one_time_max", sa.Integer(), nullable=False),
        sa.Column("recurring_min", sa.Integer(), nullable=False),
        sa.Column("recurring_max", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="LKR"),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("last_reviewed", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cost_items_recommendation_id", "cost_items", ["recommendation_id"])

    op.create_table(
        "requirement_evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("requirement_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("multiplier", sa.Numeric(3, 2), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("rationale", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "requirement_id", name="uq_evaluation_assessment_requirement"),
    )
    op.create_index("ix_requirement_evaluations_assessment_id", "requirement_evaluations", ["assessment_id"])
    op.create_index("ix_requirement_evaluations_requirement_id", "requirement_evaluations", ["requirement_id"])

    op.create_table(
        "assessment_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("overall_score_raw", sa.Numeric(8, 4), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("evidence_completeness", sa.Integer(), nullable=False),
        sa.Column("category_scores", sa.JSON(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("gaps", sa.JSON(), nullable=False),
        sa.Column("unknowns", sa.JSON(), nullable=False),
        sa.Column("cost_summary", sa.JSON(), nullable=False),
        sa.Column("scoring_version", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id"),
    )
    op.create_index("ix_assessment_results_assessment_id", "assessment_results", ["assessment_id"])

    op.create_table(
        "roadmap_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_id", sa.String(64), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("priority_tier", sa.Integer(), nullable=False),
        sa.Column("expected_gain", sa.Numeric(7, 3), nullable=False),
        sa.Column("projected_score_raw", sa.Numeric(8, 4), nullable=False),
        sa.Column("cost_snapshot", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["result_id"], ["assessment_results.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("result_id", "recommendation_id", name="uq_result_recommendation"),
    )
    op.create_index("ix_roadmap_items_recommendation_id", "roadmap_items", ["recommendation_id"])
    op.create_index("ix_roadmap_items_result_id", "roadmap_items", ["result_id"])

    op.create_table(
        "ai_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=True),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_runs_assessment_id", "ai_runs", ["assessment_id"])
    op.create_index("ix_ai_runs_operation", "ai_runs", ["operation"])
    op.create_index("ix_ai_runs_operation_created", "ai_runs", ["operation", "created_at"])


def downgrade() -> None:
    op.drop_table("ai_runs")
    op.drop_table("roadmap_items")
    op.drop_table("assessment_results")
    op.drop_table("requirement_evaluations")
    op.drop_table("cost_items")
    op.drop_table("recommendations")
    op.drop_table("requirements")
    op.drop_table("evidence_observations")
    op.drop_table("evidence_files")
    op.drop_table("evidence_requests")
    op.drop_table("assessment_questions")
    op.drop_table("question_bank")
    op.drop_table("process_steps")
    op.drop_table("assessment_answers")
    op.drop_table("assessments")
