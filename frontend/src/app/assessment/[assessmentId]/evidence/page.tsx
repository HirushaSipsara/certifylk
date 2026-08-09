"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { ErrorAlert } from "@/components/ErrorAlert";
import { AIAnalysisStatus } from "@/components/AIAnalysisStatus";
import { EvidenceObservationList } from "@/components/EvidenceObservationList";
import { FlowHeader, AssessmentIdChip } from "@/components/FlowHeader";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { LoadingState } from "@/components/LoadingState";
import { EvidenceUploadCard } from "@/components/EvidenceUploadCard";
import { SelectedSchemeBanner } from "@/components/SelectedSchemeBanner";
import { useAssessmentScheme } from "@/hooks/useAssessmentScheme";
import { api, ApiError } from "@/lib/api";
import type {
  EvidenceAnalysisResponse,
  EvidenceRequest,
  SelfAssessmentValue,
} from "@/types";

export default function EvidencePage() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;
  const router = useRouter();

  const { scheme } = useAssessmentScheme(assessmentId);
  const [requests, setRequests] = useState<EvidenceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [busyItem, setBusyItem] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<EvidenceAnalysisResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const a = await api.getAssessment(assessmentId);
        if (cancelled) return;

        // Fetch evidence plan
        try {
          const plan = await api.evidencePlan(assessmentId) as { requests?: EvidenceRequest[] };
          if (!cancelled && plan.requests) {
            setRequests(plan.requests);
            if (plan.requests.length === 0) {
              // No evidence required — advance to evidence analysis & clarifications
              await api.analyzeEvidence(assessmentId);
              router.push(`/assessment/${assessmentId}/clarification`);
              return;
            }
          }
        } catch {
          // If evidence requests already generated, fetch them from assessment
          if (a.evidence_requests && a.evidence_requests.length > 0) {
            setRequests(a.evidence_requests);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load evidence plan.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [assessmentId, router]);

  async function handleUpload(requestId: string, file: File) {
    setBusyItem(requestId);
    setError(null);
    try {
      await api.uploadEvidence(assessmentId, requestId, file);
      setRequests((prev) =>
        prev.map((r) =>
          r.id === requestId ? { ...r, status: "uploaded" as const } : r
        )
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to upload file.");
    } finally {
      setBusyItem(null);
    }
  }

  async function handleUnavailable(requestId: string) {
    setBusyItem(requestId);
    setError(null);
    try {
      await api.markUnavailable(assessmentId, requestId);
      setRequests((prev) =>
        prev.map((r) =>
          r.id === requestId ? { ...r, status: "unavailable" as const } : r
        )
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to mark item as unavailable.");
    } finally {
      setBusyItem(null);
    }
  }

  async function handleRemove(requestId: string) {
    setBusyItem(requestId);
    setError(null);
    try {
      await api.removeEvidence(assessmentId, requestId);
      setRequests((prev) =>
        prev.map((r) =>
          r.id === requestId ? { ...r, status: "requested" as const } : r
        )
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to remove evidence item.");
    } finally {
      setBusyItem(null);
    }
  }

  async function handleSelfAssessment(
    requestId: string,
    value: SelfAssessmentValue,
  ) {
    setBusyItem(requestId);
    setError(null);
    try {
      await api.saveEvidenceSelfAssessment(assessmentId, requestId, value);
      setRequests((previous) =>
        previous.map((request) =>
          request.id === requestId
            ? { ...request, self_assessment: value }
            : request,
        ),
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Failed to save the current-state response.",
      );
    } finally {
      setBusyItem(null);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const pending = requests.filter((request) => !request.self_assessment);
    if (pending.length > 0) {
      setError("Please answer the current-state question for every requirement before continuing.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await api.analyzeEvidence(assessmentId);
      setAnalysis(response);
      const reviewedRequestIds = new Set(
        response.observations.map((observation) => observation.evidence_request_id),
      );
      setRequests((previous) =>
        previous.map((request) =>
          request.status === "uploaded" && reviewedRequestIds.has(request.id)
            ? { ...request, status: "analyzed" as const }
            : request,
        ),
      );
      setSubmitting(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to analyze evidence.");
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <LoadingState message="Loading evidence checklist…" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface">
      {submitting && (
        <LoadingOverlay message="Saving your self-assessment and briefly reviewing optional uploads…" />
      )}
      <FlowHeader
        maxWidth="4xl"
        trailing={<AssessmentIdChip id={assessmentId} />}
      />

      <main className="max-w-3xl mx-auto px-5 py-10 space-y-8">
        <div className="space-y-3">
          <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider bg-emerald-100 px-3 py-1 rounded-full">
            Stage 3 of 5 · Evidence Upload
          </span>
          <h1 className="text-3xl font-bold text-ink mt-3">Evidence &amp; Documentation</h1>
          <p className="text-sm text-slate-600">
            Report your current practice for each requirement. Photos and documents are optional supporting evidence.
          </p>
          {scheme && <SelectedSchemeBanner scheme={scheme} label="Assessing Against" />}
        </div>

        {error && <ErrorAlert message={error} />}

        {analysis ? (
          <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-leaf-dark">
                Evidence stage saved
              </p>
              <h2 className="mt-2 text-2xl font-bold text-ink">
                {analysis.review_status === "complete"
                  ? "Review the AI observations"
                  : "Continue with your self-assessment"}
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Readiness can reflect your controlled current-state answers. Evidence completeness
                increases only when an uploaded item produces an accepted supporting observation.
                The deterministic scoring engine—not AI—calculates the report.
              </p>
              {analysis.provider ? <div className="mt-3">
                <AIAnalysisStatus
                  provider={analysis.provider}
                  fallback_used={analysis.fallback_used}
                />
              </div> : null}
            </div>

            {analysis.message ? (
              <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4 text-sm leading-6 text-slate-700" role="status">
                {analysis.message}
              </div>
            ) : null}

            <EvidenceObservationList observations={analysis.observations} />

            <div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:justify-between">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setAnalysis(null)}
              >
                Change uploaded evidence
              </button>
              <div className="flex flex-col gap-3 sm:flex-row">
                {analysis.failed_evidence_request_ids.length > 0 ? (
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={submitting}
                    onClick={() => {
                      setSubmitting(true);
                      setError(null);
                      void api
                        .analyzeEvidence(assessmentId)
                        .then(setAnalysis)
                        .catch((err: unknown) =>
                          setError(
                            err instanceof ApiError
                              ? err.message
                              : "Failed to retry evidence analysis.",
                          ),
                        )
                        .finally(() => setSubmitting(false));
                    }}
                  >
                    Retry optional AI review
                  </button>
                ) : null}
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => router.push(`/assessment/${assessmentId}/clarification`)}
                >
                  Continue to clarifications →
                </button>
              </div>
            </div>
          </section>
        ) : (
        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="space-y-4">
            {requests.map((req) => (
              <EvidenceUploadCard
                key={req.id}
                request={req}
                busy={busyItem === req.id}
                onUpload={(file) => handleUpload(req.id, file)}
                onUnavailable={() => handleUnavailable(req.id)}
                onSelfAssessment={(value) =>
                  handleSelfAssessment(req.id, value)
                }
                onRemove={() => handleRemove(req.id)}
              />
            ))}
          </div>

          <div className="flex items-center justify-between pt-4">
            <Link
              href={`/assessment/${assessmentId}/process`}
              className="text-sm text-slate-500 hover:text-slate-800"
            >
              ← Back to Process
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="bg-leaf text-white font-bold px-8 py-4 rounded-2xl hover:bg-ink transition-colors disabled:opacity-50 text-sm shadow-card"
            >
              Save &amp; Continue →
            </button>
          </div>
        </form>
        )}
      </main>
    </div>
  );
}
