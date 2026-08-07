"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { CategoryScoreList } from "@/components/CategoryScoreList";
import { CostBreakdownTable } from "@/components/CostBreakdownTable";
import { DisclaimerCard } from "@/components/DisclaimerCard";
import { ErrorAlert } from "@/components/ErrorAlert";
import { EvidenceSummary } from "@/components/EvidenceSummary";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { ReadinessScoreCard } from "@/components/ReadinessScoreCard";
import { RoadmapChecklist } from "@/components/RoadmapChecklist";
import { api, rememberAssessment } from "@/lib/api";
import type { AssessmentResult } from "@/types";

export default function ResultPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const router = useRouter();
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"sample" | "track2" | null>(null);

  useEffect(() => {
    api
      .getResult(assessmentId)
      .then((res) => {
        setResult(res);
        rememberAssessment(assessmentId, {
          schemeName: res.scheme_id ?? "Readiness Assessment",
        });
      })
      .catch((caught: unknown) =>
        setError(caught instanceof Error ? caught.message : "Could not load the result.")
      );
  }, [assessmentId]);

  async function loadSample() {
    setBusy("sample");
    setError(null);
    try {
      const assessment = await api.loadSample();
      rememberAssessment(assessment.id, { schemeName: "Fresh Fruit Cordial Sample" });
      router.push(assessment.result_url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load the sample.");
      setBusy(null);
    }
  }

  async function continueToTrack2() {
    setBusy("track2");
    setError(null);
    try {
      const assessment = await api.createAssessment();
      rememberAssessment(assessment.id, { track: "process_management" });
      router.push(`/process-management/${assessment.id}/business-profile`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not start Process Management assessment.");
      setBusy(null);
    }
  }

  function handlePrint() {
    window.print();
  }

  if (!result && !error) return <LoadingOverlay message="Loading your readiness roadmap…" />;

  return (
    <main className="min-h-screen bg-sand px-4 py-8 sm:py-12 print:bg-white print:p-0">
      {busy && (
        <LoadingOverlay
          message={
            busy === "sample"
              ? "Building sample assessment…"
              : "Starting Process Management assessment…"
          }
        />
      )}

      <div className="mx-auto max-w-5xl space-y-8">
        {/* Header */}
        <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end border-b border-slate-200 pb-6 print:border-b-2">
          <div>
            <div className="flex items-center gap-2">
              <Link href="/" className="font-bold text-leaf text-xl print:no-underline">
                CertifyLK
              </Link>
              <span className="text-xs bg-emerald-100 text-emerald-900 font-semibold px-2.5 py-0.5 rounded-full">
                Readiness Indicator
              </span>
            </div>
            <h1 className="mt-2 text-3xl sm:text-4xl font-bold tracking-tight text-ink">
              Readiness Report &amp; Action Roadmap
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              An explainable preparation snapshot derived from DB-sourced scheme requirements.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 print:hidden">
            <button
              type="button"
              onClick={handlePrint}
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
            >
              🖨️ Export PDF / Print
            </button>
            <button
              type="button"
              onClick={() => void loadSample()}
              className="rounded-xl border border-leaf bg-white px-4 py-2 text-sm font-bold text-leaf hover:bg-emerald-50 transition-colors"
            >
              Sample Report
            </button>
            <Link
              href="/"
              className="rounded-xl bg-leaf px-4 py-2 text-sm font-bold text-white hover:bg-ink transition-colors"
            >
              Start New Assessment
            </Link>
          </div>
        </header>

        {error && <ErrorAlert message={error} onRetry={() => window.location.reload()} />}

        {result && (
          <>
            {/* Draft Content Warning */}
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
              <span className="text-amber-500 text-lg shrink-0">⚠️</span>
              <div className="text-xs text-amber-900 leading-relaxed">
                <strong>Draft / Educational Certification Content:</strong> Requirement descriptions and cost snapshots are derived from publicly available SLSI guidance and have not been independently verified against official SLSI standard texts (`content_verified=false`). Use this report for readiness preparation only, not as official certification, legal advice, or an audit guarantee.
              </div>
            </div>

            {/* Score Overview */}
            <ReadinessScoreCard
              score={result.overall_score}
              completeness={result.evidence_completeness}
            />

            {/* Category Breakdown */}
            <section className="rounded-3xl bg-white p-6 shadow-card sm:p-8">
              <h2 className="text-lg font-bold text-ink mb-4">Category Readiness Breakdown</h2>
              <CategoryScoreList scores={result.category_scores} />
            </section>

            {/* Strengths & Gaps */}
            <EvidenceSummary
              strengths={result.strengths}
              gaps={result.gaps}
              unknowns={result.unknowns}
            />

            {/* Categorized Cost Summary Breakdown */}
            {result.cost_summary && (
              <section className="rounded-3xl bg-white p-6 shadow-card sm:p-8 space-y-4">
                <h2 className="text-lg font-bold text-ink">Estimated Cost Summary (LKR)</h2>
                <p className="text-xs text-slate-500">
                  Numeric estimates are derived strictly from reviewed scheme cost items. If a price is unavailable, &quot;Quote required&quot; is displayed. AI is never permitted to estimate costs.
                </p>

                <CostBreakdownTable summary={result.cost_summary} />
              </section>
            )}

            {/* Roadmap */}
            <section className="rounded-3xl bg-white p-6 shadow-card sm:p-8">
              <h2 className="text-lg font-bold text-ink mb-4">Prioritized Action Roadmap</h2>
              <RoadmapChecklist items={result.roadmap} />
            </section>

            {/* Track 1 -> Track 2 Handoff CTA */}
            {result.scheme_id === "SLS_MARK_CORDIAL" || result.scheme_id === "CAA_FOOD_REG" ? (
              <section className="rounded-3xl bg-indigo-50 border-2 border-indigo-200 p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 print:hidden">
                <div>
                  <span className="bg-indigo-100 text-indigo-800 text-xs font-bold px-3 py-1 rounded-full uppercase">
                    Next Step · Track 2 Process Certification
                  </span>
                  <h3 className="text-xl font-bold text-ink mt-2">
                    Assess Process &amp; System Certification (GMP / HACCP / ISO)
                  </h3>
                  <p className="text-sm text-slate-600 mt-1 max-w-xl">
                    Now that you have reviewed your Product Quality readiness, start a separate assessment for your manufacturing process management standards.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void continueToTrack2()}
                  className="bg-indigo-600 text-white font-bold px-6 py-3.5 rounded-2xl hover:bg-indigo-700 transition-colors text-sm shrink-0 shadow-card"
                >
                  Continue to Process Management Assessment →
                </button>
              </section>
            ) : null}

            {/* Legal Disclaimer */}
            <DisclaimerCard text={result.disclaimer} />
          </>
        )}
      </div>
    </main>
  );
}
