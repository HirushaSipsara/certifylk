"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AIAnalysisStatus } from "@/components/AIAnalysisStatus";
import { AssessmentShell } from "@/components/AssessmentShell";
import { ErrorAlert } from "@/components/ErrorAlert";
import { EvidenceObservationList } from "@/components/EvidenceObservationList";
import { EvidenceUploadCard } from "@/components/EvidenceUploadCard";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { useAssessment } from "@/hooks/useAssessment";
import { useLongRunningAnalysis } from "@/hooks/useLongRunningAnalysis";
import { api } from "@/lib/api";
import type { EvidenceAnalysisResponse, EvidenceRequest } from "@/types";

type BusyPhase = "analyzing" | "planning" | null;
type FailedAction = "analysis" | "planning" | null;

export default function EvidencePage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const router = useRouter();
  const { assessment, loading, error: loadError, refresh } = useAssessment(assessmentId);
  const [requests, setRequests] = useState<EvidenceRequest[]>([]);
  const [workingId, setWorkingId] = useState<string | null>(null);
  const [busyPhase, setBusyPhase] = useState<BusyPhase>(null);
  const [failedAction, setFailedAction] = useState<FailedAction>(null);
  const [analysis, setAnalysis] = useState<EvidenceAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const takingLonger = useLongRunningAnalysis(busyPhase === "analyzing");

  useEffect(() => {
    if (assessment) setRequests(assessment.evidence_requests);
  }, [assessment]);

  function resolveRequest(id: string, status: EvidenceRequest["status"]) {
    setRequests((current) => current.map((item) => item.id === id ? { ...item, status } : item));
  }

  async function upload(request: EvidenceRequest, file: File) {
    if (workingId || busyPhase) return;
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
    if (workingId || busyPhase) return;
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

  async function analyzeEvidence() {
    if (requests.some((request) => request.status === "requested") || busyPhase) return;
    setBusyPhase("analyzing");
    setFailedAction(null);
    setError(null);
    try {
      setAnalysis(await api.analyzeEvidence(assessmentId));
      setRequests((current) => current.map((request) => request.status === "uploaded" ? { ...request, status: "analyzed" } : request));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not analyze the submitted evidence.");
      setFailedAction("analysis");
    } finally {
      setBusyPhase(null);
    }
  }

  async function continueToClarifications() {
    if (busyPhase) return;
    setBusyPhase("planning");
    setFailedAction(null);
    setError(null);
    try {
      await api.clarificationPlan(assessmentId);
      router.push(`/assessment/${assessmentId}/clarification`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not prepare the final clarification questions.");
      setFailedAction("planning");
      setBusyPhase(null);
    }
  }

  if (loading) return <LoadingOverlay message="Loading your evidence requests…" />;
  const unresolved = requests.filter((request) => request.status === "requested").length;
  const reviewComplete = Boolean(analysis) || assessment?.status === "evidence_complete";
  const retry = failedAction === "analysis" ? analyzeEvidence : failedAction === "planning" ? continueToClarifications : null;

  return (
    <AssessmentShell currentStep={3} title="Add relevant evidence" description="Upload only what you have. Marking an item unavailable creates an evidence unknown—it does not automatically count as a confirmed gap.">
      {busyPhase ? (
        <LoadingOverlay
          message={busyPhase === "planning" ? "Choosing final clarification questions…" : takingLonger ? "Analysis is taking longer than expected" : "Analyzing evidence"}
        />
      ) : null}
      {loadError ? <ErrorAlert message={loadError} onRetry={() => void refresh()} /> : null}
      {error ? <div className="mb-5"><ErrorAlert message={error} onRetry={retry ? () => void retry() : undefined} /></div> : null}

      {reviewComplete ? (
        <section aria-labelledby="evidence-review-title" className="space-y-5">
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
            <h2 id="evidence-review-title" className="text-xl font-bold text-ink">Evidence analysis complete</h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">These are cautious observations from the submitted material, not official inspection conclusions.</p>
            {analysis ? <AIAnalysisStatus provider={analysis.provider} fallback_used={analysis.fallback_used} className="mt-3" /> : null}
          </div>
          {analysis ? (
            <EvidenceObservationList observations={analysis.observations} />
          ) : (
            <p className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
              Analysis was completed previously. Observation and provider details from the original response are not retained in this browser after a refresh.
            </p>
          )}
          <button type="button" onClick={() => void continueToClarifications()} disabled={Boolean(busyPhase)} className="w-full rounded-xl bg-leaf px-6 py-3 font-bold text-white hover:bg-ink disabled:opacity-50">Continue to final questions</button>
        </section>
      ) : (
        <>
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
          <button type="button" onClick={() => void analyzeEvidence()} disabled={Boolean(workingId) || Boolean(busyPhase) || unresolved > 0} className="mt-5 w-full rounded-xl bg-leaf px-6 py-3 font-bold text-white hover:bg-ink disabled:opacity-50">Analyze evidence</button>
        </>
      )}
    </AssessmentShell>
  );
}
