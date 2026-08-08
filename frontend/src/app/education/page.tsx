"use client";

import Link from "next/link";
import {
  ArrowRight,
  BadgeCheck,
  CheckCircle2,
  Factory,
  Gavel,
  Layers,
  PackageCheck,
  ShieldQuestion,
  Sparkles,
  Store,
  XCircle,
} from "lucide-react";

import { NoticeBanner } from "@/components/NoticeBanner";
import { PageHeader } from "@/components/PageHeader";
import { PageShell } from "@/components/PageShell";

const TIERS = [
  {
    label: "Mandatory by law",
    icon: Gavel,
    tone: "border-rose-200 bg-rose-50",
    dot: "text-rose-600",
    text: "Required by Sri Lankan legislation for all food businesses.",
  },
  {
    label: "Market required",
    icon: Store,
    tone: "border-amber-200 bg-amber-50",
    dot: "text-amber-600",
    text: "Routinely demanded by major buyers, supermarket chains, export markets, or tenders.",
  },
  {
    label: "Recommended",
    icon: BadgeCheck,
    tone: "border-sky-200 bg-sky-50",
    dot: "text-sky-600",
    text: "Baseline hygiene standards that unlock market access and build consumer trust.",
  },
  {
    label: "Optional",
    icon: Layers,
    tone: "border-line bg-mist",
    dot: "text-slate",
    text: "Advanced certifications for specialized export markets or scaling enterprises.",
  },
];

export default function EducationPage() {
  return (
    <PageShell maxWidth="5xl">
      <PageHeader
        eyebrow="Educational overview"
        eyebrowIcon={Sparkles}
        title="Understand food certification pathways"
        lead="A practical guide to certification standards, mandatory regulatory tiers, and readiness pathways for Sri Lankan food manufacturers."
      />

      <NoticeBanner title="Educational reference only" tone="warning" className="mt-8">
        CertifyLK is an educational preparation tool. Requirement descriptions are simplified
        implementation summaries and do not replace official standard publications from the Sri Lanka
        Standards Institution (SLSI) or legal texts from the Consumer Affairs Authority (CAA). Always
        confirm official requirements directly with SLSI or regulatory authorities.
      </NoticeBanner>

      <section className="card mt-8 space-y-5">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate">
          <span className="h-px w-6 bg-line" />
          Two pathways
        </div>
        <h2 className="font-display text-xl font-bold text-ink">
          Product Quality vs. Process &amp; System
        </h2>
        <p className="max-w-3xl text-sm leading-relaxed text-slate">
          Food certification in Sri Lanka generally falls into two categories depending on whether
          the standard applies to your finished product or your manufacturing facility.
        </p>
        <div className="grid gap-4 pt-1 md:grid-cols-2">
          <article className="rounded-2xl border border-brand-200 bg-brand-50/60 p-5">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white">
              <PackageCheck className="h-5 w-5" aria-hidden="true" />
            </span>
            <h3 className="mt-3 text-base font-semibold text-brand-900">Product Quality (Track 1)</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-slate">
              Certifies that a specific finished product consistently satisfies chemical, physical,
              microbiological, and packaging specifications set by SLSI. Also includes mandatory CAA
              food business registration.
            </p>
          </article>
          <article className="rounded-2xl border border-accent-200 bg-accent-50/70 p-5">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-accent-700 text-white">
              <Factory className="h-5 w-5" aria-hidden="true" />
            </span>
            <h3 className="mt-3 text-base font-semibold text-accent-900">Process &amp; System (Track 2)</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-slate">
              Certifies that your manufacturing facility, hygiene controls, and management processes
              comply with SLS GMP, SLS HACCP, or ISO 22000:2018.
            </p>
          </article>
        </div>
      </section>

      <section className="card mt-6 space-y-5">
        <h2 className="font-display text-xl font-bold text-ink">Understanding mandatory tiers</h2>
        <p className="max-w-3xl text-sm leading-relaxed text-slate">
          CertifyLK categorizes certification pathways into four tiers to help small food producers
          prioritize preparation.
        </p>
        <div className="grid gap-3 pt-1 sm:grid-cols-2">
          {TIERS.map((tier) => {
            const Icon = tier.icon;
            return (
              <div key={tier.label} className={`flex gap-3 rounded-2xl border p-4 ${tier.tone}`}>
                <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${tier.dot}`} aria-hidden="true" />
                <div>
                  <p className="text-sm font-semibold text-ink">{tier.label}</p>
                  <p className="mt-1 text-sm leading-relaxed text-slate">{tier.text}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="card mt-6 space-y-5">
        <h2 className="font-display text-xl font-bold text-ink">
          What CertifyLK does and does not do
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-brand-200 bg-brand-50/50 p-5">
            <div className="mb-3 flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-brand-600" aria-hidden="true" />
              <h3 className="text-sm font-semibold text-brand-900">What CertifyLK does</h3>
            </div>
            <ul className="space-y-2 text-sm leading-relaxed text-slate">
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                Evaluates your business profile and process against sourced requirements.
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                Identifies specific evidence gaps and documentation needs.
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                Provides score indicators and categorized cost roadmaps.
              </li>
            </ul>
          </div>
          <div className="rounded-2xl border border-line bg-mist p-5">
            <div className="mb-3 flex items-center gap-2">
              <XCircle className="h-5 w-5 text-slate" aria-hidden="true" />
              <h3 className="text-sm font-semibold text-ink">What CertifyLK does not do</h3>
            </div>
            <ul className="space-y-2 text-sm leading-relaxed text-slate">
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-slate/50" />
                Does not issue official certification marks or SLS licenses.
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-slate/50" />
                Does not replace official SLSI audits, laboratory testing, or inspections.
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-slate/50" />
                Does not provide formal legal representation or financial guarantees.
              </li>
            </ul>
          </div>
        </div>
      </section>

      <div className="mt-10 flex flex-col items-center gap-4 rounded-3xl border border-line bg-gradient-to-br from-ink to-ink-soft px-6 py-10 text-center">
        <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10 text-brand-200">
          <ShieldQuestion className="h-5 w-5" aria-hidden="true" />
        </span>
        <div>
          <h2 className="font-display text-xl font-bold text-white">Ready to check where you stand?</h2>
          <p className="mx-auto mt-1.5 max-w-md text-sm leading-relaxed text-white/70">
            Run a guided readiness assessment and get a prioritized roadmap in minutes.
          </p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-xl bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-400"
        >
          Start your readiness check
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      </div>
    </PageShell>
  );
}
