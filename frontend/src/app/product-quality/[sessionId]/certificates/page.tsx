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
    recommended: { label: "Recommended", cls: "bg-blue-100 text-blue-800 border-blue-200", icon: "⭐" },
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
  const color = confidence >= 0.85 ? "bg-emerald-500" : confidence >= 0.6 ? "bg-amber-400" : "bg-gray-300";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-8 text-right">{pct}%</span>
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
      className={`rounded-2xl border-2 overflow-hidden transition-all ${
        isRecommended
          ? "border-emerald-400 shadow-md shadow-emerald-100"
          : "border-gray-200 shadow-sm"
      }`}
    >
      {isRecommended && (
        <div className="bg-emerald-500 text-white text-xs font-bold px-4 py-1.5 flex items-center gap-2">
          <span>✓</span> Recommended starting point
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
            id={`expand-${decision.scheme_id}`}
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
            <div className="bg-emerald-50 rounded-xl p-3">
              <p className="text-xs font-semibold text-emerald-800 mb-1">AI reasoning</p>
              <p className="text-xs text-emerald-700 leading-relaxed">{decision.reasoning}</p>
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
              id="start-assessment-btn"
              href={`/assessment/${assessmentId}/hub`}
              className="block w-full text-center bg-emerald-600 text-white py-2.5 rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-colors"
            >
              Start assessment for {decision.scheme_name} →
            </Link>
          </div>
        )}
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
      setError(err instanceof ApiError ? err.message : "Failed to analyse your profile. Please try again.");
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
    <div className="min-h-screen bg-gradient-to-br from-[#fffaf0] via-[#f0faf5] to-[#e8f5f0]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">🍃</span>
            <span className="font-bold text-emerald-800 text-lg">CertifyLK</span>
          </Link>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="w-6 h-6 rounded-full bg-gray-200 text-gray-400 flex items-center justify-center text-xs font-bold">1</span>
            <span>→</span>
            <span className="w-6 h-6 rounded-full bg-gray-200 text-gray-400 flex items-center justify-center text-xs font-bold">2</span>
            <span>→</span>
            <span className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold">3</span>
            <span className="text-emerald-700 font-medium hidden sm:inline">Your certificates</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-12 h-12 border-4 border-emerald-400 border-t-transparent rounded-full animate-spin" />
            <p className="text-emerald-800 font-medium text-sm">
              AI is analysing your profile…
            </p>
            <p className="text-gray-400 text-xs max-w-xs text-center">
              The applicability agent is reviewing your product, business profile, and target markets against
              the certification catalogue.
            </p>
          </div>
        ) : error ? (
          <div className="text-center py-16 space-y-4">
            <div className="text-4xl">⚠️</div>
            <h1 className="text-lg font-semibold text-gray-800">Something went wrong</h1>
            <p className="text-gray-500 text-sm">{error}</p>
            <div className="flex gap-3 justify-center">
              <button
                id="retry-applicability"
                onClick={retry}
                disabled={retrying}
                className="bg-emerald-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-40"
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
              <h1 className="text-2xl sm:text-3xl font-bold text-emerald-900">
                Your applicable certificates
              </h1>
              <p className="text-gray-500 mt-2 text-sm leading-relaxed max-w-2xl">
                Based on your product and business profile, the AI has identified the following certification
                requirements. Start with the recommended path.
              </p>
            </div>

            {/* AI reasoning overview */}
            <div className="bg-white rounded-2xl border border-emerald-100 shadow-sm p-5">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-emerald-100 rounded-xl flex items-center justify-center text-base shrink-0">
                  🤖
                </div>
                <div>
                  <p className="text-xs font-semibold text-emerald-800 mb-1">
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
                    The requirement details for this scheme are derived from publicly available SLSI guidance.
                    They have not been verified against the purchased SLSI standard text.
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

            {/* Disclaimer */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-xs text-amber-700 leading-relaxed">
                <strong>Disclaimer:</strong> These decisions are AI-generated observations for readiness planning
                purposes only. They do not constitute legal advice, official certification decisions, or an audit
                finding. Certification applicability must be confirmed with SLSI, CAA, or the relevant issuing body.
              </p>
            </div>
          </>
        ) : null}
      </main>
    </div>
  );
}
