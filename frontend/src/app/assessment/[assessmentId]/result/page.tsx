"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FileDown, Sparkles } from "lucide-react";

import { CategoryScoreList } from "@/components/CategoryScoreList";
import { CostBreakdownTable } from "@/components/CostBreakdownTable";
import { DisclaimerCard } from "@/components/DisclaimerCard";
import { ErrorAlert } from "@/components/ErrorAlert";
import { EvidenceSummary } from "@/components/EvidenceSummary";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { ReadinessScoreCard } from "@/components/ReadinessScoreCard";
import { RoadmapChecklist } from "@/components/RoadmapChecklist";
import { FlowHeader, AssessmentIdChip } from "@/components/FlowHeader";
import { SelectedSchemeBanner } from "@/components/SelectedSchemeBanner";
import { VerificationWarning } from "@/components/VerificationWarning";
import { api, rememberAssessment } from "@/lib/api";
import type { AssessmentResult, SchemeChip } from "@/types";

export default function ResultPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const router = useRouter();
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [scheme, setScheme] = useState<SchemeChip | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"sample" | "track2" | null>(null);

  useEffect(() => {
    api
      .getResult(assessmentId)
      .then(async (res) => {
        setResult(res);
        rememberAssessment(assessmentId, {
          schemeName: res.scheme_id ?? "Readiness Assessment",
        });
        // Resolve scheme display name
        if (res.scheme_id) {
          try {
            const schemes = await api.listSchemes();
            const found = schemes.find((s) => s.id === res.scheme_id);
            if (found) setScheme(found);
          } catch {
            // Non-fatal: banner simply won't appear
          }
        }
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
    <main className="min-h-screen bg-surface print:bg-white print:p-0">
      {busy && (
        <LoadingOverlay
          message={
            busy === "sample"
              ? "Building sample assessment…"
              : "Starting Process Management assessment…"
          }
        />
      )}

      <FlowHeader
        maxWidth="5xl"
        trailing={
          <div className="flex items-center gap-2">
            <AssessmentIdChip id={assessmentId} />
            <Link href="/" className="btn-primary hidden px-4 py-2 text-sm sm:inline-flex print:hidden">
              Start new assessment
            </Link>
          </div>
        }
      />
      <div className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6 sm:py-10">
        <header className="flex flex-col justify-between gap-5 border-b border-slate-200 pb-7 sm:flex-row sm:items-end print:border-b-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-leaf">Readiness indicator</p>
            <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
              Readiness report &amp; action roadmap
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              An explainable preparation snapshot derived from database-sourced scheme requirements.
            </p>
            {scheme && (
              <div className="mt-3">
                <SelectedSchemeBanner scheme={scheme} label="Report for Certificate" />
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-2 print:hidden">
            <button type="button" onClick={handlePrint} className="btn-secondary px-4 py-2 text-sm">
              <FileDown className="h-4 w-4" aria-hidden="true" />
              Export / print
            </button>
            <button type="button" onClick={() => void loadSample()} className="btn-secondary px-4 py-2 text-sm">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Sample report
            </button>
          </div>
        </header>

        {error && <ErrorAlert message={error} onRetry={() => window.location.reload()} />}

        {result && (
          <>
            {/* Draft Content Warning */}
            <VerificationWarning title="Draft educational content">
              Requirement descriptions and cost snapshots are derived from publicly available SLSI guidance and have not been independently verified against official SLSI standard texts. Use this report for readiness preparation only, not as official certification, legal advice, or an audit guarantee.
            </VerificationWarning>

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
