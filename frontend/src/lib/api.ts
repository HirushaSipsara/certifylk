import type { Assessment, AssessmentResult, Question } from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

interface ApiErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    details?: Array<{ field?: string; message: string }>;
    request_id?: string;
  };
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details: Array<{ field?: string; message: string }> = [],
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!response.ok) {
    let payload: ApiErrorEnvelope = {};
    try {
      payload = (await response.json()) as ApiErrorEnvelope;
    } catch {
      payload = {};
    }
    throw new ApiError(
      payload.error?.message ?? "The request could not be completed.",
      response.status,
      payload.error?.details ?? [],
      payload.error?.request_id,
    );
  }
  return (await response.json()) as T;
}

export const api = {
  createAssessment: () =>
    apiFetch<{ id: string }>("/assessments", { method: "POST" }),
  loadSample: () =>
    apiFetch<{ id: string; result_url: string }>("/assessments/sample", {
      method: "POST",
    }),
  getAssessment: (id: string) => apiFetch<Assessment>(`/assessments/${id}`),
  saveProfile: (id: string, body: unknown) =>
    apiFetch(`/assessments/${id}/profile`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  adaptivePlan: (id: string) =>
    apiFetch<{ questions: Question[] }>(`/assessments/${id}/adaptive-plan`, {
      method: "POST",
    }),
  saveProcess: (id: string, body: unknown) =>
    apiFetch(`/assessments/${id}/process`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  analyzeProcess: (id: string) =>
    apiFetch(`/assessments/${id}/process-analysis`, { method: "POST" }),
  evidencePlan: (id: string) =>
    apiFetch(`/assessments/${id}/evidence-plan`, { method: "POST" }),
  uploadEvidence: (id: string, requestId: string, file: File) => {
    const body = new FormData();
    body.set("evidence_request_id", requestId);
    body.set("file", file);
    return apiFetch(`/assessments/${id}/evidence/upload`, {
      method: "POST",
      body,
    });
  },
  markUnavailable: (id: string, requestId: string) =>
    apiFetch(`/assessments/${id}/evidence/${requestId}/unavailable`, {
      method: "PUT",
    }),
  analyzeEvidence: (id: string) =>
    apiFetch(`/assessments/${id}/evidence-analysis`, { method: "POST" }),
  clarificationPlan: (id: string) =>
    apiFetch<{ questions: Question[] }>(
      `/assessments/${id}/clarification-plan`,
      { method: "POST" },
    ),
  saveClarifications: (id: string, body: unknown) =>
    apiFetch(`/assessments/${id}/clarifications`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  complete: (id: string) =>
    apiFetch(`/assessments/${id}/complete`, { method: "POST" }),
  getResult: (id: string) =>
    apiFetch<AssessmentResult>(`/assessments/${id}/result`),
};

export function rememberAssessment(id: string): void {
  window.localStorage.setItem("certifylk_assessment_id", id);
}
