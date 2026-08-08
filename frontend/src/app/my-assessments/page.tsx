"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { NoticeBanner } from "@/components/NoticeBanner";
import { PageShell } from "@/components/PageShell";
import { getRememberedAssessments, removeRememberedAssessment } from "@/lib/api";
import type { SavedAssessmentMeta } from "@/lib/assessment-storage";

export default function MyAssessmentsPage() {
  const [assessments, setAssessments] = useState<SavedAssessmentMeta[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const list = getRememberedAssessments();
    setAssessments(list);
    setLoading(false);
  }, []);

  function handleRemove(id: string) {
    removeRememberedAssessment(id);
    setAssessments((prev) => prev.filter((item) => item.id !== id));
  }

  return (
    <PageShell maxWidth="5xl">
      <div>
        <h1 className="section-title">My Assessments</h1>
        <p className="section-lead">
          Browser-local guest assessment recovery. Assessments started on this browser are listed
          below.
        </p>
      </div>

      <NoticeBanner title="Saved on this browser" tone="info" className="mt-6">
        CertifyLK guest assessments do not require an account or login. Your saved assessment IDs
        are stored locally in this browser&apos;s storage.
      </NoticeBanner>

      {loading ? (
        <div className="py-12 text-center text-slate-500">Loading saved assessments…</div>
      ) : assessments.length === 0 ? (
        <div className="card mt-8 text-center">
          <h2 className="text-lg font-bold text-ink">No saved assessments found</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
            You have not started any readiness assessments on this browser yet. Select a track on the
            home page to begin.
          </p>
          <Link href="/" className="btn-primary mt-6 inline-flex">
            Start New Assessment
          </Link>
        </div>
      ) : (
        <div className="mt-8 space-y-4">
          {assessments.map((item) => (
            <div
              key={item.id}
              className="card flex flex-col justify-between gap-4 sm:flex-row sm:items-center"
            >
              <div className="min-w-0">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                      item.track === "process_management"
                        ? "border-indigo-200 bg-indigo-50 text-indigo-700"
                        : "border-emerald-200 bg-emerald-50 text-emerald-800"
                    }`}
                  >
                    {item.track === "process_management" ? "Process and System" : "Product Quality"}
                  </span>
                  <span className="font-mono text-xs text-slate-400">#{item.id.slice(0, 8)}</span>
                </div>
                <h3 className="truncate text-base font-semibold text-ink">
                  {item.schemeName ?? item.productName ?? "Readiness Assessment"}
                </h3>
                <p className="mt-1 text-xs text-slate-400">
                  Last accessed: {new Date(item.lastSeenAt).toLocaleDateString()} at{" "}
                  {new Date(item.lastSeenAt).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <Link href={`/assessment/${item.id}/hub`} className="btn-primary px-4 py-2">
                  Resume
                </Link>
                <button
                  type="button"
                  onClick={() => handleRemove(item.id)}
                  className="rounded-xl border border-red-200 px-3 py-2 text-xs font-medium text-red-700 transition-colors hover:border-red-300 hover:bg-red-50"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </PageShell>
  );
}
