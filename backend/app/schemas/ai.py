import uuid
from typing import Literal

from pydantic import BaseModel, Field

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


class ProcessStageOutput(BaseModel):
    position: int = Field(ge=1, le=5)
    name: str = Field(min_length=1, max_length=200)
    tags: list[ProcessTag]
    confidence: float = Field(ge=0, le=1)


class ProcessExtractionOutput(BaseModel):
    stages: list[ProcessStageOutput] = Field(min_length=3, max_length=5)
    uncertainties: list[str] = Field(default_factory=list, max_length=10)


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


class RoadmapExplanationsOutput(BaseModel):
    explanations: list[RoadmapExplanationOutput]
