"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  ChevronDown,
  Zap,
  AlertTriangle,
  ClipboardList,
  ExternalLink,
} from "lucide-react";

import { api, ApiError } from "@/lib/api";
import type { SchemeRequirement } from "@/types";
import { FlowHeader } from "@/components/FlowHeader";
import { VerificationWarning } from "@/components/VerificationWarning";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ErrorAlert } from "@/components/ErrorAlert";

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
    return () => {
      cancelled = true;
    };
  }, [assessmentId]);

  const grouped = groupByCategory(reqs);
  const categories = Object.keys(grouped);

  return (
    <div className="min-h-screen bg-surface">
      <FlowHeader
        maxWidth="5xl"
        trailing={
          <Link
            href={`/assessment/${assessmentId}/hub`}
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 transition-colors hover:text-leaf"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Hub
          </Link>
        }
      />

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6 sm:py-10">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-leaf">Reference</p>
          <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            Scheme requirements
          </h1>
          <p className="mt-2 max-w-2xl text-slate-600">
            The requirements that make up this certification scheme, grouped by category.
          </p>
        </div>

        {hasUnverified && (
          <VerificationWarning title="Content not independently verified">
            These requirements are derived from publicly available SLSI guidance and have not been verified
            against the purchased SLSI standard text. Always consult SLSI for official requirements.
          </VerificationWarning>
        )}

        {loading ? (
          <LoadingState message="Loading requirements…" />
        ) : error ? (
          <ErrorAlert message={error} />
        ) : reqs.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="No requirements found"
            description="Run the applicability check first to link a certification scheme."
            action={
              <Link
                href={`/assessment/${assessmentId}/hub`}
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-leaf hover:text-leaf-dark"
              >
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                Back to hub
              </Link>
            }
          />
        ) : (
          <div className="space-y-8">
            {categories.map((category) => (
              <section key={category}>
                <div className="mb-3 flex items-center gap-2">
                  <h2 className="text-base font-semibold text-ink">{category}</h2>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
                    {grouped[category].length} requirement{grouped[category].length !== 1 ? "s" : ""}
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

        <VerificationWarning title="Educational tool only">
          Requirement descriptions are approximate guidance based on publicly available information. They do not
          constitute official certification requirements or an audit finding. Contact SLSI for the authoritative
          standard text.
        </VerificationWarning>
      </main>
    </div>
  );
}

function RequirementCard({ req }: { req: SchemeRequirement }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card overflow-hidden p-0">
      <button
        id={`req-${req.id}`}
        className="flex w-full items-start gap-3 px-5 py-4 text-left transition-colors hover:bg-slate-50"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className="mt-0.5 flex shrink-0 items-center gap-1.5">
          {req.safety_critical && (
            <span
              title="Safety critical requirement"
              className="flex h-6 w-6 items-center justify-center rounded-md bg-red-50 text-red-600"
            >
              <Zap className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
          )}
          {!req.content_verified && (
            <span
              title="Content not independently verified"
              className="flex h-6 w-6 items-center justify-center rounded-md bg-amber-50 text-amber-600"
            >
              <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
            </span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-ink">{req.title}</p>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            {req.clause_reference && (
              <span className="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-xs text-slate-500">
                {req.clause_reference}
              </span>
            )}
            <span className="text-xs text-slate-400">Weight: {req.weight.toFixed(1)}</span>
          </div>
        </div>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${expanded ? "rotate-180" : ""}`}
          aria-hidden="true"
        />
      </button>

      {expanded && (
        <div className="space-y-3 border-t border-slate-100 bg-slate-50/60 px-5 py-4">
          <p className="text-sm leading-relaxed text-slate-600">{req.description}</p>
          {req.source_document && (
            <div className="text-xs text-slate-400">
              <span className="font-medium text-slate-500">Source:</span> {req.source_document}
              {req.clause_reference && <span> · {req.clause_reference}</span>}
            </div>
          )}
          {req.source_url && (
            <a
              href={req.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-semibold text-leaf hover:underline"
            >
              Official reference
              <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
          )}
        </div>
      )}
    </div>
  );
}
