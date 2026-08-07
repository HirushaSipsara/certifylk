"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Assessment, SchemeChip } from "@/types";

// ── Status helpers ────────────────────────────────────────────────────────────

const STEPS = [
  { id: "profile", label: "Business Profile", icon: "🏭" },
  { id: "process", label: "Production Process", icon: "⚙️" },
  { id: "evidence", label: "Evidence Upload", icon: "📄" },
  { id: "clarification", label: "Clarifications", icon: "💬" },
  { id: "result", label: "Readiness Report", icon: "📊" },
] as const;

const PAGE_ORDER = ["profile", "process", "evidence", "clarification", "result"];

function stepIndex(page: string): number {
  return PAGE_ORDER.indexOf(page);
}

function tierBadge(tier: string) {
  const map: Record<string, { label: string; cls: string }> = {
    mandatory: { label: "Mandatory by law", cls: "bg-red-100 text-red-800 border-red-200" },
    market_required: { label: "Market required", cls: "bg-amber-100 text-amber-800 border-amber-200" },
    recommended: { label: "Recommended", cls: "bg-blue-100 text-blue-800 border-blue-200" },
    optional: { label: "Optional", cls: "bg-gray-100 text-gray-700 border-gray-200" },
  };
  const { label, cls } = map[tier] ?? { label: tier, cls: "bg-gray-100 text-gray-700 border-gray-200" };
  return (
    <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full border ${cls}`}>
      {label}
    </span>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AssessmentHubPage() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;

  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [scheme, setScheme] = useState<SchemeChip | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const a = await api.getAssessment(assessmentId);
        if (!cancelled) setAssessment(a);
        // Try to load schemes to find the linked one
        const schemes = await api.listSchemes();
        const linked = schemes.find((s) => {
          // Check if the profile_data contains a linked scheme
          const profileData = a.profile as Record<string, unknown>;
          const appDec = profileData?.applicability_decision as Record<string, unknown> | undefined;
          return appDec?.recommended_path_scheme_id === s.id;
        });
        if (!cancelled && linked) setScheme(linked);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load assessment.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [assessmentId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#fffaf0]">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-500">Loading your assessment…</p>
        </div>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#fffaf0] p-6">
        <div className="max-w-md text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h1 className="text-xl font-semibold text-gray-800 mb-2">Assessment not found</h1>
          <p className="text-gray-500 mb-6">{error ?? "This assessment could not be loaded."}</p>
          <Link href="/" className="inline-block bg-emerald-600 text-white px-5 py-2 rounded-lg hover:bg-emerald-700 transition-colors">
            Start new assessment
          </Link>
        </div>
      </div>
    );
  }

  const currentStep = stepIndex(assessment.current_page);
  const isCompleted = assessment.status === "completed";

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#fffaf0] via-[#f0faf5] to-[#e8f5f0]">
      {/* ── Header ── */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="text-2xl">🍃</span>
            <span className="font-bold text-emerald-800 text-lg group-hover:text-emerald-600 transition-colors">
              CertifyLK
            </span>
          </Link>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 font-mono hidden sm:block">
              #{assessmentId.slice(0, 8)}
            </span>
            {isCompleted && (
              <Link
                href={`/assessment/${assessmentId}/result`}
                className="bg-emerald-600 text-white text-sm px-4 py-1.5 rounded-lg hover:bg-emerald-700 transition-colors"
              >
                View Report
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* ── Page title ── */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-emerald-900">
            Assessment Hub
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            Track your progress through each step of the readiness assessment.
          </p>
        </div>

        {/* ── Certificate chip (if scheme linked) ── */}
        {scheme && (
          <div className="bg-white rounded-2xl border border-emerald-100 shadow-sm p-5 flex items-start gap-4">
            <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center text-xl shrink-0">
              🏅
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h2 className="text-base font-semibold text-emerald-900">{scheme.name}</h2>
                {tierBadge(scheme.mandatory_tier)}
              </div>
              <p className="text-sm text-gray-500 line-clamp-2">{scheme.summary}</p>
              {scheme.typical_timeline_days && (
                <p className="text-xs text-gray-400 mt-1">
                  Typical timeline: ~{Math.round(scheme.typical_timeline_days / 30)} months
                </p>
              )}
            </div>
            <Link
              href={`/assessment/${assessmentId}/hub/requirements`}
              className="text-sm text-emerald-600 hover:text-emerald-800 whitespace-nowrap font-medium transition-colors"
            >
              View requirements →
            </Link>
          </div>
        )}

        {/* ── Step progress ── */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-50">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Assessment Steps
            </h2>
          </div>
          <div className="divide-y divide-gray-50">
            {STEPS.map((step, idx) => {
              const done = idx < currentStep || isCompleted;
              const active = idx === currentStep && !isCompleted;
              const locked = idx > currentStep && !isCompleted;

              return (
                <div
                  key={step.id}
                  className={`flex items-center gap-4 px-5 py-4 transition-colors ${
                    active ? "bg-emerald-50" : done ? "hover:bg-gray-50" : ""
                  }`}
                >
                  {/* Status icon */}
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-base shrink-0 ${
                      done
                        ? "bg-emerald-500 text-white"
                        : active
                        ? "bg-emerald-100 text-emerald-700 ring-2 ring-emerald-400"
                        : "bg-gray-100 text-gray-400"
                    }`}
                  >
                    {done ? "✓" : step.icon}
                  </div>

                  {/* Label */}
                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium ${
                        done ? "text-emerald-700" : active ? "text-emerald-900" : "text-gray-400"
                      }`}
                    >
                      {step.label}
                    </p>
                    {active && (
                      <p className="text-xs text-emerald-500 mt-0.5">In progress</p>
                    )}
                  </div>

                  {/* CTA */}
                  {(active || done) && step.id !== "result" && (
                    <Link
                      href={`/assessment/${assessmentId}/${step.id}`}
                      id={`hub-step-${step.id}`}
                      className={`text-sm px-3 py-1.5 rounded-lg border transition-colors ${
                        active
                          ? "bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700"
                          : "border-gray-200 text-gray-500 hover:text-emerald-700 hover:border-emerald-200"
                      }`}
                    >
                      {active ? "Continue" : "Review"}
                    </Link>
                  )}
                  {step.id === "result" && (done || isCompleted) && (
                    <Link
                      href={`/assessment/${assessmentId}/result`}
                      id="hub-step-result"
                      className="text-sm px-3 py-1.5 rounded-lg border bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700 transition-colors"
                    >
                      View Report
                    </Link>
                  )}
                  {locked && (
                    <span className="text-xs text-gray-300">Locked</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Disclaimer ── */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <p className="text-xs text-amber-700 leading-relaxed">
            <strong>Educational tool only.</strong> CertifyLK is a readiness preparation tool, not a certification
            issuer, auditor, or official inspection body. All requirement content referencing SLS standards is
            approximate and has not been independently verified against the purchased SLSI standard text. Consult
            the Sri Lanka Standards Institution (SLSI) for official certification requirements.
          </p>
        </div>
      </main>
    </div>
  );
}
