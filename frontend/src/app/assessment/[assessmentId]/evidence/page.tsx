"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { ErrorAlert } from "@/components/ErrorAlert";
import { FlowHeader, AssessmentIdChip } from "@/components/FlowHeader";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { LoadingState } from "@/components/LoadingState";
import { EvidenceUploadCard } from "@/components/EvidenceUploadCard";
import { SelectedSchemeBanner } from "@/components/SelectedSchemeBanner";
import { useAssessmentScheme } from "@/hooks/useAssessmentScheme";
import { api, ApiError } from "@/lib/api";
import type { EvidenceRequest } from "@/types";

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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Verify all requested items have been uploaded or marked unavailable
    const pending = requests.filter((r) => r.status === "requested");
    if (pending.length > 0) {
      setError("Please upload a file or click 'I do not have this' for every requested item before continuing.");
      return;
    }

    setSubmitting(true);
    try {
      await api.analyzeEvidence(assessmentId);
      router.push(`/assessment/${assessmentId}/clarification`);
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
        <LoadingOverlay message="Analyzing photo and document evidence observations against scheme rules…" />
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
            Upload photos of your workspace, labels, water test reports, or mark items currently unavailable.
          </p>
          {scheme && <SelectedSchemeBanner scheme={scheme} label="Assessing Against" />}
        </div>

        {error && <ErrorAlert message={error} />}

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="space-y-4">
            {requests.map((req) => (
              <EvidenceUploadCard
                key={req.id}
                request={req}
                busy={busyItem === req.id}
                onUpload={(file) => handleUpload(req.id, file)}
                onUnavailable={() => handleUnavailable(req.id)}
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
              Analyze Evidence &amp; Continue →
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
