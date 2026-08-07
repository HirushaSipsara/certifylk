"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { ApplicabilityResult, SchemeDecision } from "@/types";

function TierBadge({ tier }: { tier: string }) {
  const map: Record<string, { label: string; cls: string; icon: string }> = {
    mandatory: { label: "Mandatory by law", cls: "bg-red-100 text-red-800 border-red-200", icon: "⚖️" },
    market_required: { label: "Market required", cls: "bg-amber-100 text-amber-800 border-amber-200", icon: "🏪" },
    recommended: { label: "Recommended", cls: "bg-indigo-100 text-indigo-800 border-indigo-200", icon: "⭐" },
    optional: { label: "Optional", cls: "bg-gray-100 text-gray-600 border-gray-200", icon: "💡" },
  };
  const { label, cls, icon } = map[tier] ?? map.optional;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border ${cls}`}>
      {icon} {label}
    </span>
  );
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    confidence >= 0.85 ? "bg-indigo-500" : confidence >= 0.6 ? "bg-amber-400" : "bg-gray-300";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-8 text-right">{pct}%</span>
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
      className={`rounded-2xl border-2 overflow-hidden transition-all ${
        isRecommended
          ? "border-indigo-400 shadow-md shadow-indigo-100"
          : "border-gray-200 shadow-sm"
      }`}
    >
      {isRecommended && (
        <div className="bg-indigo-600 text-white text-xs font-bold px-4 py-1.5 flex items-center gap-2">
          <span>✓</span> Recommended starting point
        </div>
      )}
      {pathway && !isRecommended && (
        <div className="bg-indigo-50 text-indigo-600 text-xs font-semibold px-4 py-1.5 border-b border-indigo-100">
          {pathway}
        </div>
      )}
      {pathway && isRecommended && (
        <div className="bg-indigo-500 text-white text-xs font-semibold px-4 py-1 border-b border-indigo-400 opacity-80">
          {pathway}
        </div>
      )}

      <div className="bg-white p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <h3 className="font-semibold text-gray-900 text-sm">{decision.scheme_name}</h3>
              <TierBadge tier={decision.tier} />
            </div>
            <p className="text-xs text-gray-500 mb-2">{decision.body_name}</p>
            <ConfidenceBar confidence={decision.confidence} />
          </div>
          <button
            id={`pm-expand-${decision.scheme_id}`}
            onClick={() => setExpanded((v) => !v)}
            className="text-gray-400 hover:text-gray-600 transition-colors text-sm"
            aria-expanded={expanded}
          >
            {expanded ? "▲" : "▼"}
          </button>
        </div>

        {expanded && (
          <div className="mt-4 space-y-3 border-t border-gray-50 pt-4">
            {decision.summary && (
              <p className="text-sm text-gray-600 leading-relaxed">{decision.summary}</p>
            )}
            <div className="bg-indigo-50 rounded-xl p-3">
              <p className="text-xs font-semibold text-indigo-800 mb-1">AI reasoning</p>
              <p className="text-xs text-indigo-700 leading-relaxed">{decision.reasoning}</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-3">
              <p className="text-xs font-semibold text-gray-600 mb-1">Source reference</p>
              <p className="text-xs text-gray-500 leading-relaxed">{decision.source_reference}</p>
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-400">
              {months && <span>⏱ ~{months} month{months !== 1 ? "s" : ""} typical timeline</span>}
            </div>
          </div>
        )}

        {isRecommended && (
          <div className="mt-4">
            <Link
              id="pm-start-assessment-btn"
              href={`/assessment/${assessmentId}/hub`}
              className="block w-full text-center bg-indigo-600 text-white py-2.5 rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-colors"
            >
              Start assessment for {decision.scheme_name} →
            </Link>
          </div>
        )}
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
        err instanceof ApiError
          ? err.message
          : "Failed to analyse your profile. Please try again.",
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
    <div className="min-h-screen bg-gradient-to-br from-[#f8f7ff] via-[#f0f4ff] to-[#e8f0ff]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-indigo-100 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">🍃</span>
            <span className="font-bold text-indigo-800 text-lg">CertifyLK</span>
          </Link>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-bold text-indigo-700">
              Track 2
            </span>
            <span>→</span>
            <span className="w-6 h-6 rounded-full bg-gray-200 text-gray-400 flex items-center justify-center text-xs font-bold">
              1
            </span>
            <span>→</span>
            <span className="w-6 h-6 rounded-full bg-indigo-500 text-white flex items-center justify-center text-xs font-bold">
              2
            </span>
            <span className="text-indigo-700 font-medium hidden sm:inline">Your certifications</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-12 h-12 border-4 border-indigo-400 border-t-transparent rounded-full animate-spin" />
            <p className="text-indigo-800 font-medium text-sm">
              AI is analysing your profile…
            </p>
            <p className="text-gray-400 text-xs max-w-xs text-center">
              The applicability agent is reviewing your business profile and target markets against the
              GMP, HACCP, and ISO 22000 certification catalogue.
            </p>
          </div>
        ) : error ? (
          <div className="text-center py-16 space-y-4">
            <div className="text-4xl">⚠️</div>
            <h1 className="text-lg font-semibold text-gray-800">Something went wrong</h1>
            <p className="text-gray-500 text-sm">{error}</p>
            <div className="flex gap-3 justify-center">
              <button
                id="pm-retry-applicability"
                onClick={retry}
                disabled={retrying}
                className="bg-indigo-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-40"
              >
                {retrying ? "Retrying…" : "Try again"}
              </button>
              <Link
                href="/"
                className="border border-gray-200 text-gray-600 px-6 py-2.5 rounded-xl text-sm hover:bg-gray-50 transition-colors"
              >
                Start over
              </Link>
            </div>
          </div>
        ) : result ? (
          <>
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 border border-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700 mb-4">
                🏭 Process &amp; System Certification
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-indigo-900">
                Your applicable certifications
              </h1>
              <p className="text-gray-500 mt-2 text-sm leading-relaxed max-w-2xl">
                Based on your business profile and target markets, the AI has determined which
                process management certifications apply. They follow a natural progression:
                GMP → HACCP → ISO 22000.
              </p>
            </div>

            {/* Certification pathway explanation */}
            <div className="bg-white rounded-2xl border border-indigo-100 shadow-sm p-5">
              <p className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-3">
                Certification pathway
              </p>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="bg-indigo-100 text-indigo-700 font-bold px-2 py-0.5 rounded-lg">GMP</span>
                <span>Foundation for all certifications</span>
                <span className="mx-2 text-gray-300">→</span>
                <span className="bg-amber-100 text-amber-700 font-bold px-2 py-0.5 rounded-lg">HACCP</span>
                <span>Required for market access</span>
                <span className="mx-2 text-gray-300">→</span>
                <span className="bg-emerald-100 text-emerald-700 font-bold px-2 py-0.5 rounded-lg">ISO 22000</span>
                <span>Export markets</span>
              </div>
            </div>

            {/* AI reasoning overview */}
            <div className="bg-white rounded-2xl border border-indigo-100 shadow-sm p-5">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-indigo-100 rounded-xl flex items-center justify-center text-base shrink-0">
                  🤖
                </div>
                <div>
                  <p className="text-xs font-semibold text-indigo-800 mb-1">
                    AI Assessment · {result.provider} ·{" "}
                    {result.fallback_used ? "fallback mode" : "primary mode"}
                  </p>
                  <p className="text-sm text-gray-600 leading-relaxed">{result.overall_reasoning}</p>
                </div>
              </div>
            </div>

            {/* Unverified content banner */}
            {result.has_unverified_content && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3">
                <span className="text-amber-500 text-lg shrink-0">⚠️</span>
                <div>
                  <p className="text-sm font-medium text-amber-800">Requirement content not independently verified</p>
                  <p className="text-xs text-amber-700 mt-0.5">
                    The requirement details for these schemes are derived from publicly available SLSI and
                    ISO guidance. They have not been verified against purchased standard texts. Always
                    confirm requirements with the issuing body before taking action.
                  </p>
                </div>
              </div>
            )}

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
            <div className="flex justify-between items-center pt-2">
              <Link
                href={`/process-management/${assessmentId}/business-profile`}
                className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
              >
                ← Edit business profile
              </Link>
            </div>

            {/* Disclaimer */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-xs text-amber-700 leading-relaxed">
                <strong>Disclaimer:</strong> These decisions are AI-generated observations for readiness planning
                purposes only. They do not constitute legal advice, official certification decisions, or an audit
                finding. Certification applicability must be confirmed with SLSI, ISO-accredited bodies, or
                the relevant issuing authority.
              </p>
            </div>
          </>
        ) : null}
      </main>
    </div>
  );
}
