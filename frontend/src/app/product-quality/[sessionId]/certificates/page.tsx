"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowRight, Check, ChevronDown, Clock, Cpu, Sparkles } from "lucide-react";

import { AIAnalysisStatus } from "@/components/AIAnalysisStatus";
import { FlowHeader, FlowSteps } from "@/components/FlowHeader";
import { LoadingState } from "@/components/LoadingState";
import { NoticeBanner } from "@/components/NoticeBanner";
import { TierBadge } from "@/components/TierBadge";
import { VerificationWarning } from "@/components/VerificationWarning";
import { api, ApiError } from "@/lib/api";
import type { ApplicabilityResult, SchemeDecision } from "@/types";

const STEPS = ["Choose product", "Business profile", "Certificates"];

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    confidence >= 0.85 ? "bg-leaf" : confidence >= 0.6 ? "bg-amber-400" : "bg-slate-300";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-xs text-slate-400">{pct}%</span>
    </div>
  );
}

function DecisionCard({
  decision,
  isRecommended,
  assessmentId,
}: {
  decision: SchemeDecision;
  isRecommended: boolean;
  assessmentId: string;
}) {
  const [expanded, setExpanded] = useState(isRecommended);
  const months = decision.typical_timeline_days
    ? Math.round(decision.typical_timeline_days / 30)
    : null;

  return (
    <div
      className={`overflow-hidden rounded-2xl border transition-all ${
        isRecommended ? "border-leaf shadow-card" : "border-slate-200 shadow-soft"
      }`}
    >
      {isRecommended ? (
        <div className="flex items-center gap-2 bg-leaf px-4 py-1.5 text-xs font-bold text-white">
          <Check className="h-3.5 w-3.5" aria-hidden="true" />
          Recommended starting point
        </div>
      ) : null}
      <div className="bg-white p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold text-ink">{decision.scheme_name}</h3>
              <TierBadge tier={decision.tier} />
            </div>
            <p className="mb-2 text-xs text-slate">{decision.body_name}</p>
            <ConfidenceBar confidence={decision.confidence} />
          </div>
          <button
            id={`expand-${decision.scheme_id}`}
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-50 hover:text-ink"
            aria-expanded={expanded}
            aria-label={expanded ? "Collapse details" : "Expand details"}
          >
            <ChevronDown
              className={`h-5 w-5 transition-transform ${expanded ? "rotate-180" : ""}`}
              aria-hidden="true"
            />
          </button>
        </div>

        {expanded ? (
          <div className="mt-4 space-y-3 border-t border-slate-100 pt-4">
            {decision.summary ? (
              <p className="text-sm leading-relaxed text-slate">{decision.summary}</p>
            ) : null}
            <div className="rounded-xl bg-leaf/5 p-3">
              <p className="mb-1 text-xs font-semibold text-leaf-dark">AI reasoning</p>
              <p className="text-xs leading-relaxed text-slate">{decision.reasoning}</p>
            </div>
            <div className="rounded-xl bg-mist p-3">
              <p className="mb-1 text-xs font-semibold text-ink">Source reference</p>
              <p className="text-xs leading-relaxed text-slate">{decision.source_reference}</p>
            </div>
            {months ? (
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Clock className="h-3.5 w-3.5" aria-hidden="true" />~{months} month
                {months !== 1 ? "s" : ""} typical timeline
              </div>
            ) : null}
          </div>
        ) : null}

        {isRecommended ? (
          <div className="mt-4">
            <Link
              id="start-assessment-btn"
              href={`/assessment/${assessmentId}/hub`}
              className="btn-primary w-full"
            >
              Start assessment for {decision.scheme_name}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function CertificatesPage() {
  const params = useParams<{ sessionId: string }>();
  const assessmentId = params.sessionId;

  const [result, setResult] = useState<ApplicabilityResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  async function runAgent() {
    try {
      const data = await api.runApplicabilityAgent(assessmentId);
      setResult(data);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to analyse your profile. Please try again.",
      );
    } finally {
      setLoading(false);
      setRetrying(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    void runAgent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessmentId]);

  function retry() {
    setError(null);
    setLoading(true);
    setRetrying(true);
    void runAgent();
  }

  return (
    <div className="min-h-screen bg-surface">
      <FlowHeader trailing={<FlowSteps steps={STEPS} current={3} tone="leaf" />} />

      <main className="mx-auto max-w-4xl space-y-8 px-4 py-10 sm:px-6">
        {loading ? (
          <LoadingState
            message="AI is analysing your profile…"
            detail="The applicability agent is reviewing your product, business profile, and target markets against the certification catalogue."
          />
        ) : error ? (
          <div className="card mx-auto max-w-md space-y-4 text-center">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-coral/10 text-coral">
              <Sparkles className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <h1 className="text-lg font-semibold text-ink">Something went wrong</h1>
              <p className="mt-1 text-sm text-slate">{error}</p>
            </div>
            <div className="flex justify-center gap-3">
              <button
                id="retry-applicability"
                type="button"
                onClick={retry}
                disabled={retrying}
                className="btn-primary"
              >
                {retrying ? "Retrying…" : "Try again"}
              </button>
              <Link href="/" className="btn-secondary">
                Start over
              </Link>
            </div>
          </div>
        ) : result ? (
          <>
            <div>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-leaf/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-leaf-dark">
                Track 1 · Product Quality
              </span>
              <h1 className="section-title mt-3">Your applicable certificates</h1>
              <p className="section-lead">
                Based on your product and business profile, the AI has identified the following
                certification requirements. Start with the recommended path.
              </p>
            </div>

            {/* AI reasoning overview */}
            <div className="card !p-5">
              <div className="flex items-start gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-leaf/10 text-leaf">
                  <Cpu className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="min-w-0">
                  <div className="mb-1.5">
                    <AIAnalysisStatus
                      provider={result.provider}
                      fallback_used={result.fallback_used}
                    />
                  </div>
                  <p className="text-sm leading-relaxed text-slate">{result.overall_reasoning}</p>
                </div>
              </div>
            </div>

            {/* Unverified content banner */}
            {result.has_unverified_content ? (
              <VerificationWarning>
                The requirement details for this scheme are derived from publicly available SLSI
                guidance. They have not been verified against the purchased SLSI standard text.
              </VerificationWarning>
            ) : null}

            {/* Decision cards */}
            <div className="space-y-4">
              {result.decisions.map((d) => (
                <DecisionCard
                  key={d.scheme_id}
                  decision={d}
                  isRecommended={d.scheme_id === result.recommended_path_scheme_id}
                  assessmentId={assessmentId}
                />
              ))}
            </div>

            {/* Disclaimer */}
            <NoticeBanner tone="warning">
              <strong>Disclaimer:</strong> These decisions are AI-generated observations for
              readiness planning purposes only. They do not constitute legal advice, official
              certification decisions, or an audit finding. Certification applicability must be
              confirmed with SLSI, CAA, or the relevant issuing body.
            </NoticeBanner>
          </>
        ) : null}
      </main>
    </div>
  );
}
