"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, ChevronDown, Clock, Cpu, Sparkles } from "lucide-react";

import { AIAnalysisStatus } from "@/components/AIAnalysisStatus";
import { FlowHeader, FlowSteps } from "@/components/FlowHeader";
import { LoadingState } from "@/components/LoadingState";
import { NoticeBanner } from "@/components/NoticeBanner";
import { TierBadge } from "@/components/TierBadge";
import { VerificationWarning } from "@/components/VerificationWarning";
import { api, ApiError } from "@/lib/api";
import type { ApplicabilityResult, SchemeDecision } from "@/types";

const STEPS = ["Business profile", "Certificates"];

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    confidence >= 0.85 ? "bg-accent-600" : confidence >= 0.6 ? "bg-amber-400" : "bg-slate-300";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-xs text-slate-400">{pct}%</span>
    </div>
  );
}

/** Scheme pathway label for Track 2 maturity order (GMP → HACCP → ISO 22000). */
const PATHWAY_LABEL: Record<string, string> = {
  SLS_GMP: "Step 1 of 3 — Foundation",
  SLS_HACCP: "Step 2 of 3 — Market Access",
  ISO_22000: "Step 3 of 3 — Export Ready",
};

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
  const pathway = PATHWAY_LABEL[decision.scheme_id];

  return (
    <div
      className={`overflow-hidden rounded-2xl border transition-all ${
        isRecommended ? "border-accent-500 shadow-card" : "border-slate-200 shadow-soft"
      }`}
    >
      {isRecommended ? (
        <div className="flex items-center gap-2 bg-accent-600 px-4 py-1.5 text-xs font-bold text-white">
          <Check className="h-3.5 w-3.5" aria-hidden="true" />
          Recommended starting point
        </div>
      ) : null}
      {pathway && !isRecommended ? (
        <div className="border-b border-accent-100 bg-accent-50 px-4 py-1.5 text-xs font-semibold text-accent-700">
          {pathway}
        </div>
      ) : null}
      {pathway && isRecommended ? (
        <div className="border-b border-accent-400 bg-accent-500 px-4 py-1 text-xs font-semibold text-white opacity-90">
          {pathway}
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
            id={`pm-expand-${decision.scheme_id}`}
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
            <div className="rounded-xl bg-accent-50 p-3">
              <p className="mb-1 text-xs font-semibold text-accent-800">AI reasoning</p>
              <p className="text-xs leading-relaxed text-accent-700">{decision.reasoning}</p>
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
              id="pm-start-assessment-btn"
              href={`/assessment/${assessmentId}/hub`}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-accent-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent-700"
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

export default function ProcessMgmtCertificatesPage() {
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
      <FlowHeader trailing={<FlowSteps steps={STEPS} current={2} tone="navy" prefix="T2" />} />

      <main className="mx-auto max-w-4xl space-y-8 px-4 py-10 sm:px-6">
        {loading ? (
          <LoadingState
            message="AI is analysing your profile…"
            detail="The applicability agent is reviewing your business profile and target markets against the GMP, HACCP, and ISO 22000 certification catalogue."
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
                id="pm-retry-applicability"
                type="button"
                onClick={retry}
                disabled={retrying}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent-700 disabled:opacity-50"
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
              <span className="inline-flex items-center gap-1.5 rounded-full bg-accent-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-accent-800">
                Track 2 · Process &amp; System
              </span>
              <h1 className="section-title mt-3">Your applicable certifications</h1>
              <p className="section-lead">
                Based on your business profile and target markets, the AI has determined which
                process management certifications apply. They follow a natural progression: GMP →
                HACCP → ISO 22000.
              </p>
            </div>

            {/* Certification pathway explanation */}
            <div className="card !p-5">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-accent-700">
                Certification pathway
              </p>
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate">
                <span className="rounded-lg bg-accent-100 px-2 py-0.5 font-bold text-accent-700">
                  GMP
                </span>
                <span>Foundation for all certifications</span>
                <ArrowRight className="mx-1 h-3.5 w-3.5 text-slate-300" aria-hidden="true" />
                <span className="rounded-lg bg-amber-100 px-2 py-0.5 font-bold text-amber-700">
                  HACCP
                </span>
                <span>Required for market access</span>
                <ArrowRight className="mx-1 h-3.5 w-3.5 text-slate-300" aria-hidden="true" />
                <span className="rounded-lg bg-brand-100 px-2 py-0.5 font-bold text-brand-700">
                  ISO 22000
                </span>
                <span>Export markets</span>
              </div>
            </div>

            {/* AI reasoning overview */}
            <div className="card !p-5">
              <div className="flex items-start gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent-100 text-accent-700">
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
                The requirement details for these schemes are derived from publicly available SLSI
                and ISO guidance. They have not been verified against purchased standard texts.
                Always confirm requirements with the issuing body before taking action.
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

            {/* Back to profile */}
            <div className="flex items-center justify-between pt-2">
              <Link
                href={`/process-management/${assessmentId}/business-profile`}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-slate transition-colors hover:text-ink"
              >
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                Edit business profile
              </Link>
            </div>

            {/* Disclaimer */}
            <NoticeBanner tone="warning">
              <strong>Disclaimer:</strong> These decisions are AI-generated observations for
              readiness planning purposes only. They do not constitute legal advice, official
              certification decisions, or an audit finding. Certification applicability must be
              confirmed with SLSI, ISO-accredited bodies, or the relevant issuing authority.
            </NoticeBanner>
          </>
        ) : null}
      </main>
    </div>
  );
}
