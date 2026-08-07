import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import AssessmentStatus, EvidenceKind, EvidenceRequestStatus, QuestionPage


class QuestionOption(BaseModel):
    value: str
    label: str


class QuestionResponse(BaseModel):
    id: str
    text: str
    options: list[QuestionOption]
    allows_other: bool
    category: str


class AssignedQuestionResponse(QuestionResponse):
    page: QuestionPage
    display_order: int


class AnswerInput(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=120)
    other_text: str | None = Field(default=None, max_length=500)


class ProfileInput(BaseModel):
    product_name: str = Field(min_length=2, max_length=150)
    food_category: Literal["processed_food", "bakery", "beverage", "spice_product", "other"]
    other_category_text: str | None = Field(default=None, max_length=150)
    production_location: Literal[
        "home_kitchen", "shared_kitchen", "small_workshop", "small_factory", "other"
    ]
    production_location_other: str | None = Field(default=None, max_length=150)
    production_scale: Literal["micro", "small", "growing"]
    worker_range: Literal["1_5", "6_10", "11_25", "26_plus"]
    packaging_type: Literal["glass_bottle", "plastic_bottle", "pouch", "box", "jar", "other"]
    packaging_type_other: str | None = Field(default=None, max_length=150)
    storage_method: Literal["room_temperature", "refrigerated", "frozen", "mixed", "other"]
    storage_method_other: str | None = Field(default=None, max_length=150)
    shelf_life_range: Literal[
        "under_one_week", "one_to_four_weeks", "one_to_six_months", "over_six_months"
    ]
    existing_certification: str = Field(min_length=1, max_length=200)
    production_record_frequency: Literal["every_batch", "sometimes", "never"]
    additional_information: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def validate_other_fields(self) -> "ProfileInput":
        conditional = [
            (self.food_category, self.other_category_text, "other_category_text"),
            (
                self.production_location,
                self.production_location_other,
                "production_location_other",
            ),
            (self.packaging_type, self.packaging_type_other, "packaging_type_other"),
            (self.storage_method, self.storage_method_other, "storage_method_other"),
        ]
        missing = [name for value, other, name in conditional if value == "other" and not other]
        if missing:
            raise ValueError(f"Provide details for: {', '.join(missing)}")
        return self


class ProcessInput(BaseModel):
    steps: list[str] = Field(min_length=5, max_length=5)
    adaptive_answers: list[AnswerInput]

    @model_validator(mode="after")
    def require_three_steps(self) -> "ProcessInput":
        self.steps = [step.strip()[:500] for step in self.steps]
        if sum(bool(step) for step in self.steps) < 3:
            raise ValueError("At least three production steps are required.")
        return self


class ClarificationInput(BaseModel):
    answers: list[AnswerInput] = Field(min_length=3, max_length=5)


class ProcessStageResponse(BaseModel):
    position: int
    name: str
    tags: list[str]
    confidence: float


class AIExecutionMetadataResponse(BaseModel):
    provider: Literal["gemini", "mock"]
    fallback_used: bool


class ProcessAnalysisResponse(AIExecutionMetadataResponse):
    stages: list[ProcessStageResponse]
    uncertainties: list[str]


class EvidenceRequestResponse(BaseModel):
    id: uuid.UUID
    evidence_type: str
    kind: EvidenceKind
    title: str
    required: bool
    status: EvidenceRequestStatus
    display_order: int


class AssessmentCreatedResponse(BaseModel):
    id: uuid.UUID
    status: AssessmentStatus
    current_page: str
    created_at: datetime


class AssessmentSummaryResponse(BaseModel):
    id: uuid.UUID
    status: AssessmentStatus
    current_page: str
    is_sample: bool
    profile: dict[str, object]
    process_steps: list[dict[str, object]]
    assigned_questions: list[AssignedQuestionResponse]
    evidence_requests: list[EvidenceRequestResponse]
    created_at: datetime
    updated_at: datetime


class ProfileSavedResponse(BaseModel):
    status: AssessmentStatus
    profile: dict[str, object]


class QuestionPlanResponse(BaseModel):
    questions: list[QuestionResponse]


class StatusResponse(BaseModel):
    status: AssessmentStatus


class EvidencePlanResponse(StatusResponse):
    requests: list[EvidenceRequestResponse]


class UploadResponse(BaseModel):
    file_id: uuid.UUID
    evidence_request_id: uuid.UUID
    status: EvidenceRequestStatus
    content_type: str
    size_bytes: int


class UnavailableResponse(BaseModel):
    evidence_request_id: uuid.UUID
    status: EvidenceRequestStatus


class ObservationResponse(BaseModel):
    id: uuid.UUID
    evidence_request_id: uuid.UUID
    requirement_id: str
    polarity: str
    text: str
    confidence: float


class EvidenceAnalysisResponse(StatusResponse, AIExecutionMetadataResponse):
    observations: list[ObservationResponse]


class ClarificationPlanResponse(StatusResponse):
    questions: list[QuestionResponse]


class SampleResponse(BaseModel):
    id: uuid.UUID
    status: AssessmentStatus
    current_page: str
    result_url: str


# ── New certification knowledge base schemas ───────────────────────────────────


class BusinessProfileInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    business_type: str = Field(min_length=1, max_length=40)
    years_operating: int | None = Field(default=None, ge=0, le=200)
    scale: str = Field(min_length=1, max_length=40)
    market: list[str] = Field(min_length=1, max_length=10)
    existing_certifications: list[str] = Field(default_factory=list, max_length=20)
    has_food_licence: str = Field(min_length=1, max_length=20)
    monthly_volume_range: str | None = Field(default=None, max_length=40)
    additional_info: str = Field(default="", max_length=2000)
    # Optional: link to an assessment already created
    assessment_id: uuid.UUID | None = Field(default=None)
    # Optional: product slug to link this profile to a product
    product_slug: str | None = Field(default=None, max_length=80)


class BusinessProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    business_type: str
    scale: str
    market: list[str]
    has_food_licence: str


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str
    display_order: int


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str
    category_id: uuid.UUID
    display_order: int


class SchemeChipResponse(BaseModel):
    id: str
    name: str
    short_code: str
    track: str
    mandatory_tier: str
    summary: str
    typical_timeline_days: int | None
    body_name: str
    active: bool


class SchemeRequirementResponse(BaseModel):
    id: str
    scheme_id: str
    category_label: str
    title: str
    description: str
    weight: float
    safety_critical: bool
    source_document: str
    clause_reference: str
    source_url: str
    content_verified: bool
    display_order: int


class SchemeDecisionResponse(BaseModel):
    scheme_id: str
    tier: str
    confidence: float
    reasoning: str
    source_reference: str
    scheme_name: str
    body_name: str
    typical_timeline_days: int | None
    summary: str


class ApplicabilityResponse(BaseModel):
    assessment_id: uuid.UUID
    overall_reasoning: str
    recommended_path_scheme_id: str | None
    decisions: list[SchemeDecisionResponse]
    provider: str
    fallback_used: bool
    has_unverified_content: bool
