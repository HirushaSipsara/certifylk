"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BookOpen,
  ClipboardCheck,
  FileSearch,
  FlaskConical,
  FolderCheck,
  Layers,
  ListChecks,
  Route,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { PageShell } from "@/components/PageShell";
import { Spinner } from "@/components/LoadingState";
import { api, rememberAssessment } from "@/lib/api";
import type { SchemeChip } from "@/types";

const HOW_IT_WORKS = [
  {
    icon: ClipboardCheck,
    title: "Tell us about your business",
    description: "Share your product, scale, and target markets in a short guided profile.",
  },
  {
    icon: Sparkles,
    title: "AI identifies the pathway",
    description: "We match your profile to applicable Sri Lankan certification schemes and explain why.",
  },
  {
    icon: FolderCheck,
    title: "Review requirements & evidence",
    description: "Work through clause-linked requirements and submit the evidence you already have.",
  },
  {
    icon: Route,
    title: "Get a readiness roadmap",
    description: "Receive a deterministic readiness indicator with prioritized, cost-aware next steps.",
  },
] as const;

const FEATURES = [
  {
    icon: FileSearch,
    title: "Targeted pathways",
    description:
      "Match your business profile and target markets to official Sri Lankan food certification pathways.",
  },
  {
    icon: ListChecks,
    title: "Explainable gap analysis",
    description:
      "Review clause-linked strengths and preparation gaps derived from reviewed scheme standards.",
  },
  {
    icon: Route,
    title: "Cost-aware roadmap",
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
    <PageShell maxWidth="7xl">
      {busy ? (
        <LoadingOverlay
          message={
            busy === "sample"
              ? "Building the Fresh Fruit Cordial sample…"
              : busy === "track2"
                ? "Setting up your process readiness check…"
                : "Starting your assessment…"
          }
          detail="This only takes a moment."
        />
      ) : null}

      {/* Hero */}
      <section className="relative overflow-hidden rounded-4xl border border-white/10 bg-night px-6 py-12 text-white shadow-card-hover sm:px-10 sm:py-16">
        <div className="pointer-events-none absolute inset-0 bg-grid opacity-40" aria-hidden="true" />
        <div
          className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-leaf/25 blur-3xl"
          aria-hidden="true"
        />
        <div className="relative max-w-3xl animate-fade-in-up">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-lime">
            <ShieldCheck className="h-3.5 w-3.5" />
            Sri Lanka food manufacturing
          </span>
          <h1 className="mt-5 font-display text-4xl font-bold leading-[1.05] tracking-tight text-balance sm:text-6xl">
            Find the right certification path.
            <span className="block text-lime">Know exactly what to do next.</span>
          </h1>
          <p className="mt-5 max-w-2xl text-pretty text-base leading-relaxed text-emerald-50/80 sm:text-lg">
            CertifyLK is AI-assisted certification readiness for Sri Lankan manufacturers. See your
            readiness gaps and a cost-aware roadmap — for SLS product standards and food-safety
            management systems.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Link
              href="/product-quality/select"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-leaf px-6 py-3.5 text-sm font-semibold text-white shadow-soft transition-all hover:bg-leaf-dark active:scale-[0.98]"
            >
              Start a readiness check
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/education"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              <BookOpen className="h-4 w-4" />
              Understand certification
            </Link>
          </div>
          <p className="mt-6 inline-flex items-center gap-2 rounded-lg bg-white/5 px-3 py-1.5 text-xs text-emerald-50/70">
            Preparation guidance only — not an official certification decision.
          </p>
        </div>
      </section>

      {error ? (
        <div className="mt-6">
          <ErrorAlert message={error} />
        </div>
      ) : null}

      {/* Track cards */}
      <section className="mt-12" aria-labelledby="tracks-heading">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 id="tracks-heading" className="font-display text-2xl font-bold text-ink sm:text-3xl">
              Choose your track
            </h2>
            <p className="section-lead">
              The two tracks stay separate — each has its own requirements and its own readiness
              score.
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {/* Track 1 — Product Quality */}
          <article className="group flex flex-col rounded-3xl border border-leaf/25 bg-white p-6 shadow-card transition-all hover:-translate-y-0.5 hover:shadow-card-hover sm:p-8">
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-leaf/10 text-leaf">
                <FlaskConical className="h-5 w-5" />
              </span>
              <span className="inline-flex rounded-full bg-leaf/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-leaf-dark">
                Track 1 · Product Quality
              </span>
            </div>
            <h3 className="mt-5 font-display text-2xl font-bold text-ink">Product Quality</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Assess readiness for product-specific Sri Lanka Standards (SLS Mark) and Consumer
              Affairs Authority (CAA) food business guidance. Currently supporting Fresh Fruit
              Cordial.
            </p>
            <div className="mt-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Available standards and schemes
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {productQualitySchemes.length > 0 ? (
                  productQualitySchemes.map((s) => <SchemePill key={s.id} tone="leaf" label={s.name} />)
                ) : (
                  <>
                    <SchemePill tone="leaf" label="SLS Mark — Fresh Fruit Cordial (SLS 187)" />
                    <SchemePill tone="leaf" label="CAA Food Registration" />
                  </>
                )}
              </div>
            </div>
            <div className="mt-8 border-t border-slate-100 pt-6">
              <Link
                href="/product-quality/select"
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-leaf px-6 py-3.5 text-sm font-semibold text-white transition-all hover:bg-leaf-dark active:scale-[0.98]"
              >
                Assess Product Quality
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          </article>

          {/* Track 2 — Process & System */}
          <article className="group flex flex-col rounded-3xl border border-navy/20 bg-white p-6 shadow-card transition-all hover:-translate-y-0.5 hover:shadow-card-hover sm:p-8">
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-navy/10 text-navy">
                <Layers className="h-5 w-5" />
              </span>
              <span className="inline-flex rounded-full bg-navy/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-navy">
                Track 2 · Process &amp; System
              </span>
            </div>
            <h3 className="mt-5 font-display text-2xl font-bold text-ink">Process and System</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Assess manufacturing-process and management-system readiness for SLS GMP, SLS HACCP,
              and ISO 22000:2018 certification.
            </p>
            <div className="mt-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Available standards and schemes
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {processManagementSchemes.length > 0 ? (
                  processManagementSchemes.map((s) => (
                    <SchemePill key={s.id} tone="navy" label={s.name} />
                  ))
                ) : (
                  <>
                    <SchemePill tone="navy" label="SLS GMP Certification" />
                    <SchemePill tone="navy" label="SLS HACCP Certification" />
                    <SchemePill tone="navy" label="ISO 22000:2018 Food Safety" />
                  </>
                )}
              </div>
            </div>
            <div className="mt-8 border-t border-slate-100 pt-6">
              <button
                id="start-track2-btn"
                type="button"
                disabled={Boolean(busy)}
                onClick={() => void startTrack2()}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-navy px-6 py-3.5 text-sm font-semibold text-white transition-all hover:bg-navy/90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {busy === "track2" ? (
                  <>
                    <Spinner className="h-4 w-4" />
                    Starting…
                  </>
                ) : (
                  <>
                    Assess Process Management
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                  </>
                )}
              </button>
            </div>
          </article>
        </div>
      </section>

      {/* How it works */}
      <section className="mt-14" aria-labelledby="how-heading">
        <h2 id="how-heading" className="font-display text-2xl font-bold text-ink sm:text-3xl">
          How CertifyLK works
        </h2>
        <p className="section-lead">Four steps from your profile to a ready-to-action roadmap.</p>
        <ol className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {HOW_IT_WORKS.map((step, index) => (
            <li
              key={step.title}
              className="relative rounded-3xl border border-slate-200/80 bg-white p-6 shadow-soft"
            >
              <div className="flex items-center justify-between">
                <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-mist text-leaf">
                  <step.icon className="h-5 w-5" />
                </span>
                <span className="font-display text-2xl font-bold text-slate-200">{index + 1}</span>
              </div>
              <h3 className="mt-4 text-base font-semibold text-ink">{step.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{step.description}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Features */}
      <section className="mt-6 grid gap-4 md:grid-cols-3">
        {FEATURES.map((feature) => (
          <div key={feature.title} className="card">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-leaf/10 text-leaf">
              <feature.icon className="h-5 w-5" />
            </span>
            <h3 className="mt-4 text-base font-semibold text-ink">{feature.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{feature.description}</p>
          </div>
        ))}
      </section>

      {/* Sample + quick links */}
      <section className="mt-6 grid items-stretch gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="flex flex-col justify-between rounded-3xl border border-leaf/20 bg-gradient-to-br from-white to-mist p-6 shadow-card sm:p-8">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-leaf/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-leaf-dark">
              <Sparkles className="h-3.5 w-3.5" />
              Live demo
            </span>
            <h3 className="mt-4 font-display text-xl font-bold text-ink">Explore a sample report</h3>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-600">
              View a completed readiness report for Fresh Fruit Cordial (SLS Mark) before starting
              your own assessment.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadSample()}
            disabled={Boolean(busy)}
            className="btn-secondary mt-6 self-start"
          >
            {busy === "sample" ? (
              <>
                <Spinner className="h-4 w-4" />
                Loading sample…
              </>
            ) : (
              <>
                <FileSearch className="h-4 w-4" />
                Load Sample Report
              </>
            )}
          </button>
        </div>

        <div className="grid gap-4">
          <QuickLink
            href="/education"
            icon={BookOpen}
            title="Understand Certification"
            description="Learn how the pathways fit together."
          />
          <QuickLink
            href="/my-assessments"
            icon={ClipboardCheck}
            title="My Assessments"
            description="Resume a readiness check on this browser."
          />
        </div>
      </section>
    </PageShell>
  );
}

function SchemePill({ label, tone }: { label: string; tone: "leaf" | "navy" }) {
  const cls =
    tone === "navy"
      ? "border-navy/20 bg-navy/5 text-navy"
      : "border-leaf/25 bg-leaf/5 text-leaf-dark";
  const dot = tone === "navy" ? "bg-navy" : "bg-leaf";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium ${cls}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}

function QuickLink({
  href,
  icon: Icon,
  title,
  description,
}: {
  href: string;
  icon: typeof BookOpen;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="group flex items-center gap-4 rounded-3xl border border-slate-200/80 bg-white p-5 shadow-soft transition-all hover:-translate-y-0.5 hover:border-leaf/30 hover:shadow-card"
    >
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-mist text-leaf">
        <Icon className="h-5 w-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-ink">{title}</p>
        <p className="mt-0.5 text-sm text-slate-500">{description}</p>
      </div>
      <ArrowRight className="h-4 w-4 shrink-0 text-slate-300 transition-all group-hover:translate-x-0.5 group-hover:text-leaf" />
    </Link>
  );
}
