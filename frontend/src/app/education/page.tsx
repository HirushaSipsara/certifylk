"use client";

import Link from "next/link";

export default function EducationPage() {
  return (
    <div className="min-h-screen bg-sand">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-5 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="text-2xl">🍃</span>
            <span className="font-bold text-emerald-800 text-lg group-hover:text-emerald-600 transition-colors">
              CertifyLK
            </span>
          </Link>
          <Link
            href="/my-assessments"
            className="text-sm font-medium text-slate-600 hover:text-emerald-700 transition-colors"
          >
            📋 My Assessments
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-5 py-10 space-y-8">
        <div>
          <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold uppercase text-leaf">
            Educational Overview
          </span>
          <h1 className="text-3xl font-bold text-ink mt-2">Understand Food Certification Pathways</h1>
          <p className="text-slate-600 mt-2 text-base leading-relaxed">
            A beginner-friendly guide to certification standards, mandatory regulatory tiers, and readiness pathways for Sri Lankan food manufacturers.
          </p>
        </div>

        {/* Notice Banner */}
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 text-xs text-amber-900 leading-relaxed">
          ⚠️ <strong>Educational Reference Only:</strong> CertifyLK is an educational preparation tool. Requirement descriptions are simplified implementation summaries and do not replace official standard publications from the Sri Lanka Standards Institution (SLSI) or legal texts from the Consumer Affairs Authority (CAA). Always confirm official requirements directly with SLSI or regulatory authorities.
        </div>

        {/* Section 1 */}
        <section className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm space-y-4">
          <h2 className="text-xl font-bold text-ink flex items-center gap-2">
            <span>🏅</span> Track 1: Product Quality vs. Track 2: Process & System
          </h2>
          <p className="text-sm text-slate-700 leading-relaxed">
            Food certification in Sri Lanka generally falls into two distinct categories depending on whether the standard applies to your physical product or your manufacturing facility:
          </p>

          <div className="grid gap-4 md:grid-cols-2 pt-2">
            <div className="bg-emerald-50/60 rounded-2xl p-5 border border-emerald-100">
              <h3 className="font-bold text-emerald-900 text-base mb-1">Product Quality (Track 1)</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Certifies that a specific finished product (such as Fresh Fruit Cordial) consistently satisfies chemical, physical, microbiological, and packaging specifications set by SLSI (e.g. SLS 187). Also includes mandatory Consumer Affairs Authority (CAA) food business registration.
              </p>
            </div>
            <div className="bg-indigo-50/60 rounded-2xl p-5 border border-indigo-100">
              <h3 className="font-bold text-indigo-900 text-base mb-1">Process & System (Track 2)</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Certifies that your manufacturing facility, hygiene controls, and management processes comply with international or national food safety system standards (SLS GMP, SLS HACCP, ISO 22000:2018).
              </p>
            </div>
          </div>
        </section>

        {/* Section 2 */}
        <section className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm space-y-4">
          <h2 className="text-xl font-bold text-ink flex items-center gap-2">
            <span>⚖️</span> Understanding Mandatory Tiers
          </h2>
          <p className="text-sm text-slate-700 leading-relaxed">
            CertifyLK categorizes certification pathways into four distinct tiers to help small food producers prioritize preparation:
          </p>

          <div className="space-y-3 pt-2 text-sm">
            <div className="flex items-start gap-3 p-3 bg-red-50 rounded-xl border border-red-100">
              <span className="font-bold text-red-800 shrink-0 min-w-[130px]">Mandatory by Law:</span>
              <span className="text-xs text-slate-700">Required by Sri Lankan legislation (e.g. Food Act No. 26 of 1980 / CAA registration) for all food businesses.</span>
            </div>
            <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-xl border border-amber-100">
              <span className="font-bold text-amber-800 shrink-0 min-w-[130px]">Market Required:</span>
              <span className="text-xs text-slate-700">Routinely demanded by major commercial buyers, supermarket chains, export markets, or government tenders.</span>
            </div>
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-xl border border-blue-100">
              <span className="font-bold text-blue-800 shrink-0 min-w-[130px]">Recommended:</span>
              <span className="text-xs text-slate-700">Highly beneficial baseline hygiene standards (such as SLS GMP) that unlock market access and build consumer trust.</span>
            </div>
            <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span className="font-bold text-gray-700 shrink-0 min-w-[130px]">Optional:</span>
              <span className="text-xs text-slate-700">Advanced international certifications (e.g. ISO 22000) for specialized export markets or scaling enterprises.</span>
            </div>
          </div>
        </section>

        {/* Section 3 */}
        <section className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm space-y-4">
          <h2 className="text-xl font-bold text-ink flex items-center gap-2">
            <span>💡</span> What CertifyLK Does and Does Not Do
          </h2>

          <div className="grid gap-4 md:grid-cols-2 text-xs leading-relaxed text-slate-700">
            <div className="bg-emerald-50/40 p-4 rounded-2xl border border-emerald-100">
              <h3 className="font-bold text-emerald-900 text-sm mb-2">What CertifyLK Does:</h3>
              <ul className="list-disc pl-4 space-y-1">
                <li>Evaluates your business profile and process against sourced requirements.</li>
                <li>Identifies specific evidence gaps and documentation needs.</li>
                <li>Provides deterministic score indicators and categorized cost roadmaps.</li>
              </ul>
            </div>
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
              <h3 className="font-bold text-slate-900 text-sm mb-2">What CertifyLK Does NOT Do:</h3>
              <ul className="list-disc pl-4 space-y-1">
                <li>Does not issue official certification marks or SLS licenses.</li>
                <li>Does not replace official SLSI audits, laboratory testing, or inspections.</li>
                <li>Does not provide formal legal representation or financial guarantees.</li>
              </ul>
            </div>
          </div>
        </section>

        <div className="text-center pt-4">
          <Link
            href="/"
            className="inline-block bg-leaf text-white px-8 py-4 rounded-2xl font-bold text-sm hover:bg-ink transition-colors"
          >
            Start Your Readiness Check →
          </Link>
        </div>
      </main>
    </div>
  );
}
