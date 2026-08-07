"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { SchemeRequirement } from "@/types";

// Group requirements by category_label
function groupByCategory(reqs: SchemeRequirement[]): Record<string, SchemeRequirement[]> {
  const result: Record<string, SchemeRequirement[]> = {};
  for (const req of reqs) {
    const key = req.category_label;
    if (!result[key]) result[key] = [];
    result[key].push(req);
  }
  return result;
}

export default function RequirementsPage() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;
  const [reqs, setReqs] = useState<SchemeRequirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasUnverified, setHasUnverified] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await api.getAssessmentSchemeRequirements(assessmentId);
        if (!cancelled) {
          setReqs(data);
          setHasUnverified(data.some((r) => !r.content_verified));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load requirements.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [assessmentId]);

  const grouped = groupByCategory(reqs);
  const categories = Object.keys(grouped);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#fffaf0] via-[#f0faf5] to-[#e8f5f0]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <Link
            href={`/assessment/${assessmentId}/hub`}
            className="text-sm text-emerald-600 hover:text-emerald-800 transition-colors flex items-center gap-1"
          >
            ← Hub
          </Link>
          <span className="text-gray-300">|</span>
          <h1 className="font-semibold text-emerald-900 text-sm sm:text-base">
            Scheme Requirements
          </h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Unverified content warning */}
        {hasUnverified && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3">
            <span className="text-amber-500 text-lg shrink-0">⚠️</span>
            <div>
              <p className="text-sm font-medium text-amber-800">Content not independently verified</p>
              <p className="text-xs text-amber-700 mt-0.5">
                These requirements are derived from publicly available SLSI guidance and have not been
                verified against the purchased SLSI standard text. Always consult SLSI for official requirements.
              </p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-gray-500">{error}</p>
          </div>
        ) : reqs.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-dashed border-gray-200">
            <div className="text-4xl mb-3">📋</div>
            <p className="text-gray-500 text-sm">
              No requirements found. Run the applicability check first to link a certification scheme.
            </p>
            <Link
              href={`/assessment/${assessmentId}/hub`}
              className="inline-block mt-4 text-sm text-emerald-600 hover:text-emerald-800"
            >
              ← Back to Hub
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {categories.map((category) => (
              <section key={category}>
                <div className="flex items-center gap-2 mb-3">
                  <h2 className="text-base font-semibold text-emerald-900">{category}</h2>
                  <span className="text-xs text-gray-400">
                    ({grouped[category].length} requirement{grouped[category].length !== 1 ? "s" : ""})
                  </span>
                </div>
                <div className="space-y-3">
                  {grouped[category].map((req) => (
                    <RequirementCard key={req.id} req={req} />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}

        {/* Disclaimer */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <p className="text-xs text-amber-700 leading-relaxed">
            <strong>Educational tool only.</strong> Requirement descriptions are approximate guidance based on
            publicly available information. They do not constitute official certification requirements or an audit
            finding. Contact SLSI for the authoritative standard text.
          </p>
        </div>
      </main>
    </div>
  );
}

function RequirementCard({ req }: { req: SchemeRequirement }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      <button
        id={`req-${req.id}`}
        className="w-full text-left px-5 py-4 flex items-start gap-3 hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2 shrink-0 mt-0.5">
          {req.safety_critical && (
            <span
              title="Safety critical requirement"
              className="text-red-500 text-xs font-bold"
            >
              ⚡
            </span>
          )}
          {!req.content_verified && (
            <span
              title="Content not independently verified"
              className="text-amber-400 text-xs"
            >
              ⚠️
            </span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-800">{req.title}</p>
          <div className="flex flex-wrap gap-2 mt-1">
            {req.clause_reference && (
              <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded">
                {req.clause_reference}
              </span>
            )}
            <span className="text-xs text-gray-400">
              Weight: {req.weight.toFixed(1)}
            </span>
          </div>
        </div>
        <span className="text-gray-400 text-sm">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="border-t border-gray-50 px-5 py-4 bg-gray-50/50 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">{req.description}</p>
          {req.source_document && (
            <div className="text-xs text-gray-400">
              <span className="font-medium">Source:</span> {req.source_document}
              {req.clause_reference && <span> · {req.clause_reference}</span>}
            </div>
          )}
          {req.source_url && (
            <a
              href={req.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-emerald-600 hover:underline"
            >
              Official reference ↗
            </a>
          )}
        </div>
      )}
    </div>
  );
}
