"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { DisclaimerCard } from "@/components/DisclaimerCard";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { PageShell } from "@/components/PageShell";
import { api, rememberAssessment } from "@/lib/api";
import type { SchemeChip } from "@/types";

const FEATURES = [
  {
    title: "Targeted Pathways",
    description:
      "Match your business profile and target markets to official Sri Lankan food certification pathways.",
  },
  {
    title: "Explainable Gap Analysis",
    description:
      "Review clause-linked strengths and preparation gaps derived from reviewed scheme standards.",
  },
  {
    title: "Cost-Aware Roadmap",
    description:
      "Prioritize actions with clear cost breakdowns and projected readiness improvements.",
  },
] as const;

export default function LandingPage() {
  const router = useRouter();
  const [busy, setBusy] = useState<"start" | "sample" | "track2" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [schemes, setSchemes] = useState<SchemeChip[]>([]);

  useEffect(() => {
    let cancelled = false;
    api
      .listSchemes()
      .then((data) => {
        if (!cancelled) setSchemes(data);
      })
      .catch(() => {
        // Fallback gracefully if API is unseeded or down initially
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function startTrack2() {
    if (busy) return;
    setBusy("track2");
    setError(null);
    try {
      const assessment = await api.createAssessment();
      rememberAssessment(assessment.id, { track: "process_management" });
      router.push(`/process-management/${assessment.id}/business-profile`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not start the assessment.");
      setBusy(null);
    }
  }

  async function loadSample() {
    if (busy) return;
    setBusy("sample");
    setError(null);
    try {
      const assessment = await api.loadSample();
      rememberAssessment(assessment.id, {
        track: "product_quality",
        schemeName: "Fresh Fruit Cordial Sample",
      });
      router.push(assessment.result_url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load the sample.");
      setBusy(null);
    }
  }

  const productQualitySchemes = schemes.filter((s) => s.track === "product_quality" || !s.track);
  const processManagementSchemes = schemes.filter((s) => s.track === "process_management");

  return (
    <PageShell>
      {busy ? (
        <LoadingOverlay
          message={
            busy === "sample"
              ? "Building the Fresh Fruit Cordial sample…"
              : busy === "track2"
                ? "Setting up your process readiness check…"
                : "Starting your assessment…"
          }
        />
      ) : null}

      <div className="max-w-3xl">
        <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-leaf">
          Sri Lanka Food Manufacturing
        </span>
        <h1 className="mt-5 text-4xl font-bold tracking-tight text-ink sm:text-5xl">
          Certification Readiness Platform
        </h1>
        <p className="section-lead mt-4">
          Determine your preparation readiness for SLS-related product standards and certification
          schemes with an explainable, cost-aware roadmap.
        </p>
      </div>

      {error ? (
        <div className="mt-6">
          <ErrorAlert message={error} />
        </div>
      ) : null}

      <div className="mt-10 grid gap-6 lg:grid-cols-2 lg:gap-8">
        <article className="card flex flex-col justify-between border-leaf/30">
          <div>
            <span className="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-leaf">
              Track 1 · Product Quality
            </span>
            <h2 className="mt-4 text-2xl font-bold text-ink">Product Quality</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Assess readiness for product-specific Sri Lanka Standards (SLS Mark) and Consumer
              Affairs Authority (CAA) food business guidance.
            </p>
            <div className="mt-6">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Available standards and schemes
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {productQualitySchemes.length > 0 ? (
                  productQualitySchemes.map((s) => (
                    <span
                      key={s.id}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-xs font-medium text-emerald-900"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      {s.name}
                    </span>
                  ))
                ) : (
                  <>
                    <span className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-xs font-medium text-emerald-900">
                      SLS Mark — Fresh Fruit Cordial (SLS 187)
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-xs font-medium text-emerald-900">
                      CAA Food Registration
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
          <div className="mt-8 border-t border-slate-100 pt-6">
            <Link href="/product-quality/select" className="btn-primary block w-full text-center">
              Assess Product Quality
            </Link>
          </div>
        </article>

        <article className="card flex flex-col justify-between border-indigo-200">
          <div>
            <span className="inline-flex rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-700">
              Track 2 · Process and System
            </span>
            <h2 className="mt-4 text-2xl font-bold text-ink">Process and System</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Assess manufacturing-process and management-system readiness for SLS GMP, SLS HACCP,
              and ISO 22000:2018 certification.
            </p>
            <div className="mt-6">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Available standards and schemes
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {processManagementSchemes.length > 0 ? (
                  processManagementSchemes.map((s) => (
                    <span
                      key={s.id}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50/80 px-3 py-1.5 text-xs font-medium text-indigo-900"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                      {s.name}
                    </span>
                  ))
                ) : (
                  <>
                    <span className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50/80 px-3 py-1.5 text-xs font-medium text-indigo-900">
                      SLS GMP Certification
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50/80 px-3 py-1.5 text-xs font-medium text-indigo-900">
                      SLS HACCP Certification
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50/80 px-3 py-1.5 text-xs font-medium text-indigo-900">
                      ISO 22000:2018 Food Safety
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
          <div className="mt-8 border-t border-slate-100 pt-6">
            <button
              id="start-track2-btn"
              type="button"
              disabled={Boolean(busy)}
              onClick={() => void startTrack2()}
              className="block w-full rounded-xl bg-indigo-600 px-6 py-3.5 text-center text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Assess Process Management
            </button>
          </div>
        </article>
      </div>

      <section className="card mt-10">
        <h2 className="text-xl font-bold text-ink">What CertifyLK offers</h2>
        <div className="mt-6 grid gap-6 md:grid-cols-3">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="rounded-xl border border-slate-100 bg-slate-50/60 p-5">
              <h3 className="text-base font-semibold text-ink">{feature.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="mt-8 grid items-start gap-6 lg:grid-cols-[1fr_0.85fr]">
        <section className="card border-emerald-100">
          <h3 className="text-lg font-bold text-ink">Explore sample assessment</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            View a completed readiness report for Fresh Fruit Cordial (SLS Mark) before starting
            your own assessment.
          </p>
          <button
            type="button"
            onClick={() => void loadSample()}
            disabled={Boolean(busy)}
            className="btn-secondary mt-6 disabled:opacity-50"
          >
            Load Sample Report
          </button>
        </section>
        <DisclaimerCard />
      </div>
    </PageShell>
  );
}
