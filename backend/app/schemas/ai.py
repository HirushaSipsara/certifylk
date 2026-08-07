import re
import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_model_text(value: str) -> str:
    return CONTROL_CHARACTERS.sub("", value).strip()


def require_clean_model_text(value: str) -> str:
    cleaned = clean_model_text(value)
    if not cleaned:
        raise ValueError("Model text must not be empty")
    return cleaned


ProcessTag = Literal[
    "receiving",
    "supplier_control",
    "washing",
    "preparation",
    "cooking",
    "cooling",
    "filling",
    "packaging",
    "storage",
    "distribution",
]

APPROVED_PROCESS_TAGS: set[ProcessTag] = {
    "receiving",
    "supplier_control",
    "washing",
    "preparation",
    "cooking",
    "cooling",
    "filling",
    "packaging",
    "storage",
    "distribution",
}


class QuestionPlanOutput(BaseModel):
    question_ids: list[str]
    reason: str = Field(max_length=500)

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, value: str) -> str:
        return require_clean_model_text(value)


class ProcessStageOutput(BaseModel):
    position: int = Field(ge=1, le=5)
    name: str = Field(min_length=1, max_length=200)
    tags: list[ProcessTag] = Field(min_length=1, max_length=4)
    confidence: float = Field(ge=0, le=1)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return require_clean_model_text(value)


class ProcessExtractionOutput(BaseModel):
    stages: list[ProcessStageOutput] = Field(min_length=3, max_length=5)
    uncertainties: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("uncertainties")
    @classmethod
    def sanitize_uncertainties(cls, values: list[str]) -> list[str]:
        return [clean_model_text(value)[:500] for value in values if clean_model_text(value)]


class EvidenceInput(BaseModel):
    request_id: uuid.UUID
    evidence_type: str
    requirement_ids: list[str]
    content_type: str
    safe_data_summary: str
    data_base64: str = Field(default="", repr=False)


class EvidenceObservationOutput(BaseModel):
    evidence_request_id: uuid.UUID
    requirement_id: str
    polarity: Literal["supports", "concern", "unclear"]
    text: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0, le=1)

    @field_validator("text")
    @classmethod
    def sanitize_text(cls, value: str) -> str:
        return require_clean_model_text(value)


class EvidenceAnalysisOutput(BaseModel):
    observations: list[EvidenceObservationOutput] = Field(default_factory=list, max_length=30)


class RoadmapExplanationInput(BaseModel):
    recommendation_id: str
    title: str
    implementation_steps: list[str]
    affected_titles: list[str]


class RoadmapExplanationOutput(BaseModel):
    recommendation_id: str
    explanation: str = Field(min_length=1, max_length=1000)

    @field_validator("explanation")
    @classmethod
    def sanitize_explanation(cls, value: str) -> str:
        return require_clean_model_text(value)


class RoadmapExplanationsOutput(BaseModel):
    explanations: list[RoadmapExplanationOutput]


# ── Applicability Reasoning Agent ─────────────────────────────────────────────


class SchemeDecision(BaseModel):
    """AI decision about whether a specific certification scheme applies."""

    scheme_id: str = Field(min_length=1, max_length=64)
    tier: Literal["mandatory", "market_required", "recommended", "optional"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1, max_length=500)
    source_reference: str = Field(min_length=1, max_length=200)

    @field_validator("scheme_id")
    @classmethod
    def sanitize_scheme_id(cls, value: str) -> str:
        cleaned = clean_model_text(value)
        if not cleaned:
            raise ValueError("scheme_id must not be empty")
        return cleaned

    @field_validator("reasoning")
    @classmethod
    def sanitize_reasoning(cls, value: str) -> str:
        return require_clean_model_text(value)

    @field_validator("source_reference")
    @classmethod
    def sanitize_source_reference(cls, value: str) -> str:
        return require_clean_model_text(value)


class ApplicabilityDecisionOutput(BaseModel):
    """Ranked list of certification scheme decisions from the Applicability Reasoning Agent."""

    decisions: list[SchemeDecision] = Field(min_length=1, max_length=10)
    overall_reasoning: str = Field(min_length=1, max_length=1000)
    recommended_path_scheme_id: str | None = Field(default=None, max_length=64)

    @field_validator("overall_reasoning")
    @classmethod
    def sanitize_overall_reasoning(cls, value: str) -> str:
        return require_clean_model_text(value)
