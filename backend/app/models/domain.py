import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import (
    AssessmentPage,
    AssessmentStatus,
    EvidenceKind,
    EvidenceRequestStatus,
    ObservationPolarity,
    QuestionPage,
    RequirementCategory,
    RequirementStatus,
)


def enum_type(enum_class: type[Any], name: str) -> Enum:
    return Enum(
        enum_class, name=name, native_enum=False, values_callable=lambda e: [x.value for x in e]
    )


class Assessment(TimestampMixin, Base):
    __tablename__ = "assessments"
    __table_args__ = (Index("ix_assessments_status_created", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    status: Mapped[AssessmentStatus] = mapped_column(
        enum_type(AssessmentStatus, "assessment_status"),
        default=AssessmentStatus.DRAFT_PROFILE,
        nullable=False,
        index=True,
    )
    current_page: Mapped[AssessmentPage] = mapped_column(
        enum_type(AssessmentPage, "assessment_page"),
        default=AssessmentPage.PROFILE,
        nullable=False,
    )
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    profile_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    process_analysis: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"
    __table_args__ = (
        UniqueConstraint("assessment_id", "page", "key", name="uq_answer_assessment_page_key"),
        Index("ix_answers_assessment_created", "assessment_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page: Mapped[str] = mapped_column(String(32), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProcessStep(TimestampMixin, Base):
    __tablename__ = "process_steps"
    __table_args__ = (
        UniqueConstraint("assessment_id", "position", name="uq_step_assessment_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(200))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))


class QuestionBank(Base):
    __tablename__ = "question_bank"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    allows_other: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    product_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    process_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    requirement_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    page_eligibility: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id", "question_id", "page", name="uq_assessment_question_page"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        ForeignKey("question_bank.id"), nullable=False, index=True
    )
    page: Mapped[QuestionPage] = mapped_column(
        enum_type(QuestionPage, "question_page"), nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    planning_rationale: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    answered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    question: Mapped[QuestionBank] = relationship(lazy="joined")


class EvidenceRequest(TimestampMixin, Base):
    __tablename__ = "evidence_requests"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id", "evidence_type", name="uq_evidence_request_assessment_type"
        ),
        Index("ix_evidence_request_assessment_status", "assessment_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[EvidenceKind] = mapped_column(enum_type(EvidenceKind, "evidence_kind"))
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    requirement_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[EvidenceRequestStatus] = mapped_column(
        enum_type(EvidenceRequestStatus, "evidence_request_status"),
        default=EvidenceRequestStatus.REQUESTED,
        nullable=False,
        index=True,
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)


class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    storage_key: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    original_name: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvidenceObservation(Base):
    __tablename__ = "evidence_observations"
    __table_args__ = (Index("ix_observation_assessment_created", "assessment_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evidence_files.id", ondelete="SET NULL"), index=True
    )
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("requirements.id"), nullable=False, index=True
    )
    polarity: Mapped[ObservationPolarity] = mapped_column(
        enum_type(ObservationPolarity, "observation_polarity"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    category: Mapped[RequirementCategory] = mapped_column(
        enum_type(RequirementCategory, "requirement_category"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    safety_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    applicability_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    evaluation_rule: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    implementation_steps: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    requirement_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    priority_base: Mapped[int] = mapped_column(Integer, nullable=False)
    is_capex: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cost_note: Mapped[str] = mapped_column(String(500), nullable=False)
    last_reviewed: Mapped[date] = mapped_column(Date, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CostItem(Base):
    __tablename__ = "cost_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    one_time_min: Mapped[int] = mapped_column(Integer, nullable=False)
    one_time_max: Mapped[int] = mapped_column(Integer, nullable=False)
    recurring_min: Mapped[int] = mapped_column(Integer, nullable=False)
    recurring_max: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="LKR", nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_reviewed: Mapped[date] = mapped_column(Date, nullable=False)
    recommendation: Mapped[Recommendation] = relationship(lazy="joined")


class RequirementEvaluation(TimestampMixin, Base):
    __tablename__ = "requirement_evaluations"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id", "requirement_id", name="uq_evaluation_assessment_requirement"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("requirements.id"), nullable=False, index=True
    )
    status: Mapped[RequirementStatus] = mapped_column(
        enum_type(RequirementStatus, "requirement_status"), nullable=False
    )
    multiplier: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    evidence_references: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    rationale: Mapped[str] = mapped_column(String(1000), nullable=False)
    requirement: Mapped[Requirement] = relationship(lazy="joined")


class AssessmentResult(TimestampMixin, Base):
    __tablename__ = "assessment_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    overall_score_raw: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_completeness: Mapped[int] = mapped_column(Integer, nullable=False)
    category_scores: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    strengths: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    gaps: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    unknowns: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    cost_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(30), nullable=False)


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    __table_args__ = (
        UniqueConstraint("result_id", "recommendation_id", name="uq_result_recommendation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("recommendations.id"), nullable=False, index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    priority_tier: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_gain: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    projected_score_raw: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    cost_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    explanation: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recommendation: Mapped[Recommendation] = relationship(lazy="joined")


class AIRun(Base):
    __tablename__ = "ai_runs"
    __table_args__ = (Index("ix_ai_runs_operation_created", "operation", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assessments.id", ondelete="SET NULL"), index=True
    )
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
