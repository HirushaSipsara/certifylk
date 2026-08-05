"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { DisclaimerCard } from "@/components/DisclaimerCard";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { api, rememberAssessment } from "@/lib/api";

export default function LandingPage() {
  const router = useRouter();
  const [busy, setBusy] = useState<"start" | "sample" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function startAssessment() {
    if (busy) return;
    setBusy("start");
    setError(null);
    try {
      const assessment = await api.createAssessment();
      rememberAssessment(assessment.id);
      router.push(`/assessment/${assessment.id}/profile`);
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
      rememberAssessment(assessment.id);
      router.push(assessment.result_url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load the sample.");
      setBusy(null);
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-sand">
      {busy ? (
        <LoadingOverlay
          message={busy === "sample" ? "Building the chilli-paste sample…" : "Starting your assessment…"}
        />
      ) : null}
      <div className="mx-auto grid min-h-screen max-w-6xl items-center gap-12 px-5 py-12 lg:grid-cols-[1.15fr_0.85fr] lg:px-10">
        <section>
          <span className="inline-flex rounded-full bg-lime px-4 py-2 text-sm font-bold text-ink">
            Built for small Sri Lankan food businesses
          </span>
          <h1 className="mt-6 text-5xl font-bold tracking-tight text-ink sm:text-7xl">
            Certify<span className="text-leaf">LK</span>
          </h1>
          <p className="mt-6 max-w-2xl text-xl leading-8 text-slate-700">
            Understand your preparation readiness for SLS-related food certification and get a prioritized, cost-aware action roadmap.
          </p>
          <p className="mt-4 text-sm font-semibold text-slate-500">About 10–15 minutes · No account required</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={() => void startAssessment()}
              disabled={Boolean(busy)}
              className="rounded-2xl bg-leaf px-7 py-4 text-lg font-bold text-white shadow-card hover:bg-ink disabled:opacity-50"
            >
              Start Assessment
            </button>
            <button
              type="button"
              onClick={() => void loadSample()}
              disabled={Boolean(busy)}
              className="rounded-2xl border-2 border-leaf px-7 py-4 font-bold text-leaf hover:bg-emerald-50 disabled:opacity-50"
            >
              Load Sample Assessment
            </button>
          </div>
          {error ? <div className="mt-5"><ErrorAlert message={error} /></div> : null}
        </section>
        <section className="rounded-[2rem] border border-emerald-100 bg-white p-6 shadow-card sm:p-8">
          <h2 className="text-2xl font-bold text-ink">A clear four-step check</h2>
          <ol className="mt-6 space-y-5">
            {[
              ["01", "Tell us about your product"],
              ["02", "Describe five production steps"],
              ["03", "Add relevant evidence—or mark it unavailable"],
              ["04", "Answer final clarifications and view your roadmap"],
            ].map(([number, label]) => (
              <li key={number} className="flex items-center gap-4">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-emerald-100 font-bold text-leaf">{number}</span>
                <span className="font-semibold text-slate-700">{label}</span>
              </li>
            ))}
          </ol>
          <div className="mt-7"><DisclaimerCard /></div>
        </section>
      </div>
    </main>
  );
}
