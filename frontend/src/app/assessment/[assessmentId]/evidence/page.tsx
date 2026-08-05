"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AssessmentShell } from "@/components/AssessmentShell";
import { ErrorAlert } from "@/components/ErrorAlert";
import { EvidenceUploadCard } from "@/components/EvidenceUploadCard";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { useAssessment } from "@/hooks/useAssessment";
import { api } from "@/lib/api";
import type { EvidenceRequest } from "@/types";

export default function EvidencePage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const router = useRouter();
  const { assessment, loading, error: loadError, refresh } = useAssessment(assessmentId);
  const [requests, setRequests] = useState<EvidenceRequest[]>([]);
  const [workingId, setWorkingId] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (assessment) setRequests(assessment.evidence_requests);
  }, [assessment]);

  function resolveRequest(id: string, status: EvidenceRequest["status"]) {
    setRequests((current) => current.map((item) => item.id === id ? { ...item, status } : item));
  }

  async function upload(request: EvidenceRequest, file: File) {
    if (workingId || analyzing) return;
    setWorkingId(request.id);
    setError(null);
    try {
      await api.uploadEvidence(assessmentId, request.id, file);
      resolveRequest(request.id, "uploaded");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not upload this file.");
    } finally {
      setWorkingId(null);
    }
  }

  async function unavailable(request: EvidenceRequest) {
    if (workingId || analyzing) return;
    setWorkingId(request.id);
    setError(null);
    try {
      await api.markUnavailable(assessmentId, request.id);
      resolveRequest(request.id, "unavailable");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update this evidence request.");
    } finally {
      setWorkingId(null);
    }
  }

  async function continueAssessment() {
    if (requests.some((request) => request.status === "requested") || analyzing) return;
    setAnalyzing(true);
    setError(null);
    try {
      await api.analyzeEvidence(assessmentId);
      await api.clarificationPlan(assessmentId);
      router.push(`/assessment/${assessmentId}/clarification`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not analyze the submitted evidence.");
      setAnalyzing(false);
    }
  }

  if (loading) return <LoadingOverlay message="Loading your evidence requests…" />;
  const unresolved = requests.filter((request) => request.status === "requested").length;

  return (
    <AssessmentShell currentStep={3} title="Add relevant evidence" description="Upload only what you have. Marking an item unavailable creates an evidence unknown—it does not automatically count as a confirmed gap.">
      {analyzing ? <LoadingOverlay message="Reviewing evidence and choosing final clarifications…" /> : null}
      {loadError ? <ErrorAlert message={loadError} onRetry={() => void refresh()} /> : null}
      {error ? <div className="mb-5"><ErrorAlert message={error} /></div> : null}
      <div className="space-y-4">
        {requests.map((request) => (
          <EvidenceUploadCard
            key={request.id}
            request={request}
            busy={workingId === request.id}
            onUpload={(file) => upload(request, file)}
            onUnavailable={() => unavailable(request)}
          />
        ))}
      </div>
      <p className="mt-5 text-sm text-slate-600">{unresolved ? `${unresolved} item${unresolved === 1 ? "" : "s"} still need an upload or “I do not have this”.` : "All evidence requests are resolved."}</p>
      <button type="button" onClick={() => void continueAssessment()} disabled={Boolean(workingId) || analyzing || unresolved > 0} className="mt-5 w-full rounded-xl bg-leaf px-6 py-3 font-bold text-white hover:bg-ink disabled:opacity-50">Analyze evidence and continue</button>
    </AssessmentShell>
  );
}
