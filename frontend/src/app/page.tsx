"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { DisclaimerCard } from "@/components/DisclaimerCard";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { api, rememberAssessment } from "@/lib/api";
import type { SchemeChip } from "@/types";

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

  const productQualitySchemes = schemes.filter(
    (s) => s.track === "product_quality" || !s.track
  );
  const processManagementSchemes = schemes.filter(
    (s) => s.track === "process_management"
  );

  return (
    <main className="min-h-screen bg-sand">
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

      {/* Top Navbar with Navigation Links */}
      <header className="border-b border-emerald-100 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="mx-auto max-w-6xl px-5 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="text-2xl">🍃</span>
            <span className="font-bold text-emerald-800 text-lg group-hover:text-emerald-600 transition-colors">
              CertifyLK
            </span>
          </Link>
          <div className="flex items-center gap-4 text-sm font-medium">
            <Link
              href="/my-assessments"
              className="text-slate-600 hover:text-emerald-700 transition-colors"
            >
              📋 My Assessments
            </Link>
            <Link
              href="/education"
              className="text-slate-600 hover:text-emerald-700 transition-colors"
            >
              📖 Understand Certification
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-5 py-10 lg:px-10">
        {/* Header Hero */}
        <div className="max-w-3xl">
          <span className="inline-flex rounded-full bg-lime px-4 py-1.5 text-sm font-bold text-ink">
            Sri Lanka Food Manufacturing Certification Readiness
          </span>
          <h1 className="mt-6 text-5xl font-bold tracking-tight text-ink sm:text-6xl">
            Certify<span className="text-leaf">LK</span>
          </h1>
          <p className="mt-4 text-xl leading-relaxed text-slate-700">
            Determine your preparation readiness for SLS-related product standards and certification schemes with an explainable, cost-aware roadmap.
          </p>
        </div>

        {error ? (
          <div className="mt-6">
            <ErrorAlert message={error} />
          </div>
        ) : null}

        {/* Two Tracks Grid */}
        <div className="mt-10 grid gap-8 md:grid-cols-2">
          {/* Track 1: Product Quality Certification */}
          <div className="flex flex-col justify-between rounded-3xl border-2 border-leaf bg-white p-8 shadow-card">
            <div>
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold uppercase text-leaf">
                  Track 1 · Product Quality
                </span>
                <span className="text-2xl">🏅</span>
              </div>
              <h2 className="mt-4 text-2xl font-bold text-ink">
                Product Quality
              </h2>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Assess readiness for product-specific Sri Lanka Standards (SLS Mark) and Consumer Affairs Authority (CAA) food business guidance.
              </p>

              {/* Live Scheme Chips */}
              <div className="mt-6 space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Available Standards & Schemes
                </p>
                <div className="flex flex-wrap gap-2">
                  {productQualitySchemes.length > 0 ? (
                    productQualitySchemes.map((s) => (
                      <span
                        key={s.id}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-xs font-medium text-emerald-900"
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        {s.name}
                      </span>
                    ))
                  ) : (
                    <>
                      <span className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-xs font-medium text-emerald-900">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        SLS Mark — Fresh Fruit Cordial (SLS 187)
                      </span>
                      <span className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-xs font-medium text-emerald-900">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        CAA Food Registration
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-100">
              <Link
                href="/product-quality/select"
                className="block w-full text-center rounded-2xl bg-leaf px-6 py-4 text-base font-bold text-white shadow-card hover:bg-ink transition-colors"
              >
                Assess Product Quality →
              </Link>
            </div>
          </div>

          {/* Track 2: Process Management Certification */}
          <div className="flex flex-col justify-between rounded-3xl border-2 border-indigo-200 bg-white p-8 shadow-card">
            <div>
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-bold uppercase text-indigo-700">
                  Track 2 · Process & System
                </span>
                <span className="text-2xl">🏭</span>
              </div>
              <h2 className="mt-4 text-2xl font-bold text-ink">
                Process & System
              </h2>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Assess manufacturing-process and management-system readiness for SLS GMP, SLS HACCP, and ISO 22000:2018 certification.
              </p>

              {/* Scheme Chips */}
              <div className="mt-6 space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Available Standards & Schemes
                </p>
                <div className="flex flex-wrap gap-2">
                  {processManagementSchemes.length > 0 ? (
                    processManagementSchemes.map((s) => (
                      <span
                        key={s.id}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-indigo-200 bg-indigo-50/80 px-3 py-1.5 text-xs font-medium text-indigo-900"
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                        {s.name}
                      </span>
                    ))
                  ) : (
                    <>
                      <span className="inline-flex items-center gap-1.5 rounded-xl border border-indigo-200 bg-indigo-50/80 px-3 py-1.5 text-xs font-medium text-indigo-900">
                        <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                        SLS GMP Certification
                      </span>
                      <span className="inline-flex items-center gap-1.5 rounded-xl border border-indigo-200 bg-indigo-50/80 px-3 py-1.5 text-xs font-medium text-indigo-900">
                        <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                        SLS HACCP Certification
                      </span>
                      <span className="inline-flex items-center gap-1.5 rounded-xl border border-indigo-200 bg-indigo-50/80 px-3 py-1.5 text-xs font-medium text-indigo-900">
                        <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                        ISO 22000:2018 Food Safety
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-100">
              <button
                id="start-track2-btn"
                type="button"
                disabled={Boolean(busy)}
                onClick={() => void startTrack2()}
                className="block w-full text-center rounded-2xl bg-indigo-600 px-6 py-4 text-base font-bold text-white shadow-card hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Assess Process Management →
              </button>
            </div>
          </div>
        </div>

        {/* About & Features Section */}
        <div className="mt-12 rounded-3xl bg-white p-8 border border-slate-100 shadow-sm">
          <h2 className="text-xl font-bold text-ink mb-4">About CertifyLK & What We Offer</h2>
          <div className="grid gap-6 md:grid-cols-3 text-sm text-slate-600">
            <div>
              <span className="text-2xl block mb-2">🎯</span>
              <h3 className="font-semibold text-ink text-base mb-1">Targeted Pathways</h3>
              <p>Match your business profile and target markets to official Sri Lankan food certification pathways.</p>
            </div>
            <div>
              <span className="text-2xl block mb-2">📊</span>
              <h3 className="font-semibold text-ink text-base mb-1">Explainable Gap Analysis</h3>
              <p>Review clause-linked strengths and preparation gaps derived from reviewed scheme standards.</p>
            </div>
            <div>
              <span className="text-2xl block mb-2">💰</span>
              <h3 className="font-semibold text-ink text-base mb-1">Cost-Aware Roadmap</h3>
              <p>Prioritize actions with clear cost breakdowns (body fees, lab testing, capex, opex) and projected score gains.</p>
            </div>
          </div>
        </div>

        {/* Sample Section & Educational Disclaimer */}
        <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_0.8fr] items-start">
          <div className="rounded-3xl bg-white p-8 border border-emerald-100 shadow-sm">
            <h3 className="text-lg font-bold text-ink mb-2">Explore Sample Assessment</h3>
            <p className="text-sm text-slate-600 leading-relaxed mb-6">
              Want to see a completed assessment and readiness report first? View the read-only sample report generated for Fresh Fruit Cordial (SLS Mark).
            </p>
            <button
              type="button"
              onClick={() => void loadSample()}
              disabled={Boolean(busy)}
              className="inline-flex items-center gap-2 rounded-2xl border-2 border-leaf px-6 py-3 font-bold text-leaf hover:bg-emerald-50 disabled:opacity-50 text-sm"
            >
              Load Sample Report →
            </button>
          </div>

          <div>
            <DisclaimerCard />
          </div>
        </div>
      </div>
    </main>
  );
}
