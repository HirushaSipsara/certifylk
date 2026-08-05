"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { CategoryScoreList } from "@/components/CategoryScoreList";
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
  const [sampleBusy, setSampleBusy] = useState(false);

  useEffect(() => {
    api.getResult(assessmentId).then(setResult).catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Could not load the result."));
  }, [assessmentId]);

  async function loadSample() {
    setSampleBusy(true);
    setError(null);
    try {
      const assessment = await api.loadSample();
      rememberAssessment(assessment.id);
      router.push(assessment.result_url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load the sample.");
      setSampleBusy(false);
    }
  }

  if (!result && !error) return <LoadingOverlay message="Loading your readiness roadmap…" />;

  return (
    <main className="min-h-screen bg-sand px-4 py-8 sm:py-12">
      {sampleBusy ? <LoadingOverlay message="Building a fresh sample assessment…" /> : null}
      <div className="mx-auto max-w-5xl space-y-8">
        <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <Link href="/" className="font-bold text-leaf">CertifyLK</Link>
            <h1 className="mt-2 text-4xl font-bold tracking-tight text-ink">Your readiness roadmap</h1>
            <p className="mt-2 text-slate-600">An explainable preparation snapshot based on what you submitted.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/" className="rounded-xl bg-leaf px-4 py-2 font-bold text-white hover:bg-ink">Restart Assessment</Link>
            <button type="button" onClick={() => void loadSample()} className="rounded-xl border border-leaf px-4 py-2 font-bold text-leaf hover:bg-emerald-50">Load Sample Assessment</button>
          </div>
        </header>
        {error ? <ErrorAlert message={error} onRetry={() => window.location.reload()} /> : null}
        {result ? (
          <>
            <ReadinessScoreCard score={result.overall_score} completeness={result.evidence_completeness} />
            <section className="rounded-3xl bg-white p-6 shadow-card sm:p-8"><CategoryScoreList scores={result.category_scores} /></section>
            <EvidenceSummary strengths={result.strengths} gaps={result.gaps} unknowns={result.unknowns} />
            <section className="rounded-3xl bg-white p-6 shadow-card sm:p-8"><RoadmapChecklist items={result.roadmap} /></section>
            <DisclaimerCard text={result.disclaimer} />
          </>
        ) : null}
      </div>
    </main>
  );
}
