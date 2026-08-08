"use client";

import Link from "next/link";

import { NoticeBanner } from "@/components/NoticeBanner";
import { PageShell } from "@/components/PageShell";

export default function EducationPage() {
  return (
    <PageShell maxWidth="5xl">
      <div>
        <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-leaf">
          Educational Overview
        </span>
        <h1 className="section-title mt-3">Understand Food Certification Pathways</h1>
        <p className="section-lead">
          A practical guide to certification standards, mandatory regulatory tiers, and readiness
          pathways for Sri Lankan food manufacturers.
        </p>
      </div>

      <NoticeBanner title="Educational reference only" tone="warning" className="mt-8">
        CertifyLK is an educational preparation tool. Requirement descriptions are simplified
        implementation summaries and do not replace official standard publications from the Sri Lanka
        Standards Institution (SLSI) or legal texts from the Consumer Affairs Authority (CAA). Always
        confirm official requirements directly with SLSI or regulatory authorities.
      </NoticeBanner>

      <section className="card mt-8 space-y-4">
        <h2 className="text-xl font-bold text-ink">Track 1: Product Quality vs. Track 2: Process and System</h2>
        <p className="text-sm leading-relaxed text-slate-700">
          Food certification in Sri Lanka generally falls into two categories depending on whether
          the standard applies to your finished product or your manufacturing facility.
        </p>
        <div className="grid gap-4 pt-2 md:grid-cols-2">
          <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-5">
            <h3 className="mb-1 text-base font-semibold text-emerald-900">Product Quality (Track 1)</h3>
            <p className="text-sm leading-relaxed text-slate-600">
              Certifies that a specific finished product consistently satisfies chemical, physical,
              microbiological, and packaging specifications set by SLSI. Also includes mandatory CAA
              food business registration.
            </p>
          </div>
          <div className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-5">
            <h3 className="mb-1 text-base font-semibold text-indigo-900">Process and System (Track 2)</h3>
            <p className="text-sm leading-relaxed text-slate-600">
              Certifies that your manufacturing facility, hygiene controls, and management processes
              comply with SLS GMP, SLS HACCP, or ISO 22000:2018.
            </p>
          </div>
        </div>
      </section>

      <section className="card mt-6 space-y-4">
        <h2 className="text-xl font-bold text-ink">Understanding mandatory tiers</h2>
        <p className="text-sm leading-relaxed text-slate-700">
          CertifyLK categorizes certification pathways into four tiers to help small food producers
          prioritize preparation.
        </p>
        <div className="space-y-3 pt-2">
          {[
            {
              label: "Mandatory by law",
              tone: "border-red-100 bg-red-50 text-red-800",
              text: "Required by Sri Lankan legislation for all food businesses.",
            },
            {
              label: "Market required",
              tone: "border-amber-100 bg-amber-50 text-amber-900",
              text: "Routinely demanded by major buyers, supermarket chains, export markets, or tenders.",
            },
            {
              label: "Recommended",
              tone: "border-blue-100 bg-blue-50 text-blue-800",
              text: "Baseline hygiene standards that unlock market access and build consumer trust.",
            },
            {
              label: "Optional",
              tone: "border-slate-200 bg-slate-50 text-slate-700",
              text: "Advanced certifications for specialized export markets or scaling enterprises.",
            },
          ].map((tier) => (
            <div key={tier.label} className={`rounded-xl border p-4 ${tier.tone}`}>
              <p className="text-sm font-semibold">{tier.label}</p>
              <p className="mt-1 text-sm leading-relaxed text-slate-700">{tier.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="card mt-6 space-y-4">
        <h2 className="text-xl font-bold text-ink">What CertifyLK does and does not do</h2>
        <div className="grid gap-4 text-sm leading-relaxed text-slate-700 md:grid-cols-2">
          <div className="rounded-xl border border-emerald-100 bg-emerald-50/40 p-4">
            <h3 className="mb-2 text-sm font-semibold text-emerald-900">What CertifyLK does</h3>
            <ul className="list-disc space-y-1 pl-4">
              <li>Evaluates your business profile and process against sourced requirements.</li>
              <li>Identifies specific evidence gaps and documentation needs.</li>
              <li>Provides score indicators and categorized cost roadmaps.</li>
            </ul>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <h3 className="mb-2 text-sm font-semibold text-slate-900">What CertifyLK does not do</h3>
            <ul className="list-disc space-y-1 pl-4">
              <li>Does not issue official certification marks or SLS licenses.</li>
              <li>Does not replace official SLSI audits, laboratory testing, or inspections.</li>
              <li>Does not provide formal legal representation or financial guarantees.</li>
            </ul>
          </div>
        </div>
      </section>

      <div className="pt-6 text-center">
        <Link href="/" className="btn-primary">
          Start Your Readiness Check
        </Link>
      </div>
    </PageShell>
  );
}
