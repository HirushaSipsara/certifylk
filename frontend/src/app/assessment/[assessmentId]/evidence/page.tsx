"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { AIAnalysisStatus } from "@/components/AIAnalysisStatus";
import { ErrorAlert } from "@/components/ErrorAlert";

import { EvidenceObservationList } from "@/components/EvidenceObservationList";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { api, ApiError } from "@/lib/api";
import type { Assessment, EvidenceObservation, EvidenceRequest, SchemeChip } from "@/types";

export default function EvidencePage() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;
  const router = useRouter();

  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [scheme, setScheme] = useState<SchemeChip | null>(null);
  const [requests, setRequests] = useState<EvidenceRequest[]>([]);
  const [observations, setObservations] = useState<EvidenceObservation[]>([]);
  const [analysisProvider, setAnalysisProvider] = useState<{ provider: string; fallback_used: bool } | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadingId, setUploadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reviewMode, setReviewMode] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const a = await api.getAssessment(assessmentId);
        if (cancelled) return;
        setAssessment(a);
        setRequests(a.evidence_requests ?? []);

        // Load linked scheme
        const schemes = await api.listSchemes();
        const linked = schemes.find((s) => {
          const profileData = a.profile as Record<string, unknown>;
          const appDec = profileData?.applicability_decision as Record<string, unknown> | undefined;
          return appDec?.recommended_path_scheme_id === s.id;
        });
        if (!cancelled && linked) setScheme(linked);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load evidence requests.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [assessmentId]);

  async function handleFileUpload(requestId: string, file: File) {
    setError(null);
    setUploadingId(requestId);
    try {
      await api.uploadEvidence(assessmentId, requestId, file);
      // Reload assessment state
      const updated = await api.getAssessment(assessmentId);
      setRequests(updated.evidence_requests ?? []);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to upload file.");
    } finally {
      setUploadingId(null);
    }
  }

  async function handleMarkUnavailable(requestId: string) {
    setError(null);
    try {
      await api.markUnavailable(assessmentId, requestId);
      const updated = await api.getAssessment(assessmentId);
      setRequests(updated.evidence_requests ?? []);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to mark evidence as unavailable.");
    }
  }

  async function handleAnalyzeEvidence() {
    setError(null);
    setAnalyzing(true);
    try {
      const result = await api.analyzeEvidence(assessmentId);
      setObservations(result.observations ?? []);
      setAnalysisProvider({
        provider: result.provider,
        fallback_used: result.fallback_used,
      });
      setReviewMode(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Evidence analysis failed. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleContinueToClarifications() {
    setError(null);
    try {
      const plan = await api.clarificationPlan(assessmentId);
      if (plan.questions && plan.questions.length > 0) {
        router.push(`/assessment/${assessmentId}/clarification`);
      } else {
        // If no clarification questions required, proceed directly to completion
        await api.complete(assessmentId);
        router.push(`/assessment/${assessmentId}/result`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to prepare clarification plan.");
    }
  }

  const allResolved = requests.length > 0 && requests.every((r) => r.status !== "requested");

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-sand">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-500">Loading evidence requests…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-sand">
      {analyzing && <LoadingOverlay message="Analyzing uploaded evidence against scheme requirements…" />}

      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-5 py-4 flex items-center justify-between">
          <Link href={`/assessment/${assessmentId}/hub`} className="flex items-center gap-2 group">
            <span className="text-2xl">🍃</span>
            <span className="font-bold text-emerald-800 text-lg">CertifyLK</span>
          </Link>
          <span className="text-xs font-mono text-slate-400">#{assessmentId.slice(0, 8)}</span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-5 py-10 space-y-8">
        {/* Header Title */}
        <div>
          <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider bg-emerald-100 px-3 py-1 rounded-full">
            Stage 3 of 5 · Evidence Upload
          </span>
          <h1 className="text-3xl font-bold text-ink mt-3">Evidence Collection</h1>
          <p className="text-sm text-slate-600 mt-1">
            Provide photos or documents matching the requirement expectations below, or mark items unavailable.
          </p>
        </div>

        {/* Draft Warning Banner */}
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
          <span className="text-amber-500 text-lg shrink-0">⚠️</span>
          <div className="text-xs text-amber-900 leading-relaxed">
            <strong>Draft / educational requirement catalogue:</strong> Evidence expectations and observations are for readiness preparation only. CertifyLK does not issue official compliance findings.
          </div>
        </div>

        {error && <ErrorAlert message={error} />}

        {/* Review Mode vs Upload Mode */}
        {reviewMode ? (
          <div className="bg-white rounded-3xl border border-emerald-200 p-8 space-y-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-xl font-bold text-ink">Evidence Analysis Observations</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Observations extracted by grounded AI analysis over supplied evidence.
                </p>
              </div>
              {analysisProvider && (
                <AIAnalysisStatus
                  provider={analysisProvider.provider}
                  fallbackUsed={analysisProvider.fallback_used}
                />
              )}
            </div>

            <EvidenceObservationList observations={observations} />

            <div className="flex items-center justify-between pt-6 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setReviewMode(false)}
                className="text-sm text-slate-600 hover:text-slate-900 border border-slate-200 px-4 py-2 rounded-xl"
              >
                ← Back to Uploads
              </button>
              <button
                type="button"
                onClick={() => void handleContinueToClarifications()}
                className="bg-leaf text-white font-bold px-8 py-3.5 rounded-2xl hover:bg-ink transition-colors text-sm shadow-card"
              >
                Continue to Clarifications →
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {requests.map((request) => {
              const isUploaded = request.status === "uploaded" || request.status === "analyzed";
              const isUnavailable = request.status === "unavailable";
              const isUploading = uploadingId === request.id;

              return (
                <div
                  key={request.id}
                  className={`bg-white rounded-3xl border p-6 sm:p-8 transition-all shadow-sm ${
                    isUploaded
                      ? "border-emerald-300 bg-emerald-50/20"
                      : isUnavailable
                      ? "border-slate-200 bg-slate-50/50"
                      : "border-slate-200"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                          {request.kind === "photo" ? "📷 Photo" : "📄 Document"}
                        </span>
                        {isUploaded && (
                          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                            ✓ Uploaded
                          </span>
                        )}
                        {isUnavailable && (
                          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-700">
                            Unavailable
                          </span>
                        )}
                      </div>
                      <h3 className="text-lg font-bold text-ink mt-1">{request.title}</h3>
                      {request.requirement_ids && request.requirement_ids.length > 0 && (
                        <p className="text-xs text-slate-400 font-mono mt-0.5">
                          Requirements: {request.requirement_ids.join(", ")}
                        </p>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-3 shrink-0">
                      {request.status === "requested" && (
                        <>
                          <label
                            className={`cursor-pointer bg-leaf text-white text-xs font-bold px-4 py-2.5 rounded-xl hover:bg-ink transition-colors ${
                              isUploading ? "opacity-50 pointer-events-none" : ""
                            }`}
                          >
                            {isUploading ? "Uploading…" : "Upload File"}
                            <input
                              type="file"
                              accept="image/jpeg,image/png,image/webp,application/pdf"
                              className="hidden"
                              onChange={(e) => {
                                const file = e.target.files?.[0];
                                if (file) void handleFileUpload(request.id, file);
                              }}
                            />
                          </label>
                          <button
                            type="button"
                            onClick={() => void handleMarkUnavailable(request.id)}
                            className="text-xs text-slate-500 hover:text-slate-800 border border-slate-200 px-3 py-2.5 rounded-xl transition-colors"
                          >
                            I do not have this
                          </button>
                        </>
                      )}

                      {(isUploaded || isUnavailable) && (
                        <span className="text-xs text-slate-500 font-medium">
                          {isUploaded ? "Ready for analysis" : "Marked unavailable"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Run Analysis Action */}
            <div className="flex items-center justify-between pt-6 border-t border-slate-200">
              <Link href={`/assessment/${assessmentId}/hub`} className="text-sm text-slate-500 hover:text-slate-800">
                ← Back to Hub
              </Link>
              <button
                type="button"
                disabled={!allResolved || analyzing}
                onClick={() => void handleAnalyzeEvidence()}
                className="bg-leaf text-white font-bold px-8 py-4 rounded-2xl hover:bg-ink transition-colors disabled:opacity-40 text-sm shadow-card"
              >
                Analyze Evidence &amp; Review Observations →
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
