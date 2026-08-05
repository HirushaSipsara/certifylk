import uuid
from decimal import Decimal

from pydantic import BaseModel


class CategoryScoreResponse(BaseModel):
    category: str
    label: str
    score_raw: Decimal
    score: int
    weight: int


class RequirementSummaryResponse(BaseModel):
    requirement_id: str
    title: str
    status: str
    rationale: str
    evidence_references: list[str]


class CostRangeResponse(BaseModel):
    min: int
    max: int
    currency: str


class RoadmapItemResponse(BaseModel):
    recommendation_id: str
    title: str
    implementation_steps: list[str]
    priority: int
    one_time_cost: CostRangeResponse
    recurring_cost: CostRangeResponse
    cost_note: str
    last_reviewed: str
    expected_gain: float
    projected_score: int
    explanation: str


class CostSummaryResponse(BaseModel):
    one_time_min: int
    one_time_max: int
    recurring_min: int
    recurring_max: int
    currency: str


class ResultResponse(BaseModel):
    assessment_id: uuid.UUID
    overall_score_raw: Decimal
    overall_score: int
    evidence_completeness: int
    category_scores: list[CategoryScoreResponse]
    strengths: list[RequirementSummaryResponse]
    gaps: list[RequirementSummaryResponse]
    unknowns: list[RequirementSummaryResponse]
    roadmap: list[RoadmapItemResponse]
    cost_summary: CostSummaryResponse
    disclaimer: str


class CompletionSummary(BaseModel):
    overall_score_raw: Decimal
    overall_score: int
    evidence_completeness: int
    roadmap_count: int


class CompletionResponse(BaseModel):
    status: str
    result: CompletionSummary
