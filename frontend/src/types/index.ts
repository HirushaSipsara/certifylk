export type AssessmentStatus =
  | "draft_profile"
  | "profile_complete"
  | "process_complete"
  | "evidence_pending"
  | "evidence_complete"
  | "clarification_pending"
  | "ready_to_score"
  | "completed"
  | "failed";

export interface QuestionOption {
  value: string;
  label: string;
}

export interface Question {
  id: string;
  text: string;
  options: QuestionOption[];
  allows_other: boolean;
  category: string;
  page?: "adaptive" | "clarification";
  display_order?: number;
}

export interface EvidenceRequest {
  id: string;
  evidence_type: string;
  kind: "photo" | "document";
  title: string;
  required: boolean;
  status: "requested" | "uploaded" | "unavailable" | "analyzed";
  display_order: number;
}

export interface AIExecutionMetadata {
  provider?: "gemini" | "mock";
  fallback_used?: boolean;
}

export interface ProcessAnalysisResponse extends AIExecutionMetadata {
  stages: Array<{
    position: number;
    name: string;
    tags: string[];
    confidence: number;
  }>;
  uncertainties: string[];
}

export interface EvidenceObservation {
  id: string;
  evidence_request_id: string;
  requirement_id: string;
  polarity: string;
  text: string;
  confidence: number;
}

export interface EvidenceAnalysisResponse extends AIExecutionMetadata {
  status: AssessmentStatus;
  observations: EvidenceObservation[];
}

export interface Assessment {
  id: string;
  status: AssessmentStatus;
  current_page: string;
  is_sample: boolean;
  profile: Record<string, unknown>;
  process_steps: Array<{ position: number; text: string }>;
  assigned_questions: Question[];
  evidence_requests: EvidenceRequest[];
  created_at: string;
  updated_at: string;
}

export interface RequirementSummary {
  requirement_id: string;
  title: string;
  status: "confirmed" | "partial" | "gap" | "unknown";
  rationale: string;
  evidence_references: string[];
}

export interface CategoryScore {
  category: string;
  label: string;
  score_raw: string;
  score: number;
  weight: number;
}

export interface RoadmapItem {
  recommendation_id: string;
  title: string;
  implementation_steps: string[];
  priority: number;
  one_time_cost: { min: number; max: number; currency: "LKR" };
  recurring_cost: { min: number; max: number; currency: "LKR" };
  cost_note: string;
  last_reviewed: string;
  expected_gain: number;
  projected_score: number;
  explanation: string;
}

export interface AssessmentResult {
  assessment_id: string;
  overall_score_raw: string;
  overall_score: number;
  evidence_completeness: number;
  category_scores: CategoryScore[];
  strengths: RequirementSummary[];
  gaps: RequirementSummary[];
  unknowns: RequirementSummary[];
  roadmap: RoadmapItem[];
  cost_summary: {
    one_time_min: number;
    one_time_max: number;
    recurring_min: number;
    recurring_max: number;
    currency: "LKR";
  };
  disclaimer: string;
}
