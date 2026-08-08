"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Factory,
  FolderClock,
  PackageCheck,
  Plus,
  Trash2,
} from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { NoticeBanner } from "@/components/NoticeBanner";
import { PageHeader } from "@/components/PageHeader";
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
      <PageHeader
        title="My assessments"
        description="Browser-local guest assessment recovery. Assessments started on this browser are listed below."
        actions={
          <Link href="/" className="btn-primary">
            <Plus className="h-4 w-4" aria-hidden="true" />
            New assessment
          </Link>
        }
      />

      <NoticeBanner title="Saved on this browser" tone="info" className="mt-6">
        CertifyLK guest assessments do not require an account or login. Your saved assessment IDs
        are stored locally in this browser&apos;s storage.
      </NoticeBanner>

      {loading ? (
        <div className="py-16 text-center text-sm text-slate">Loading saved assessments…</div>
      ) : assessments.length === 0 ? (
        <EmptyState
          className="mt-8"
          icon={FolderClock}
          title="No saved assessments found"
          description="You have not started any readiness assessments on this browser yet. Select a track on the home page to begin."
          action={
            <Link href="/" className="btn-primary">
              Start new assessment
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          }
        />
      ) : (
        <ul className="mt-8 space-y-4">
          {assessments.map((item) => {
            const isTrack2 = item.track === "process_management";
            const TrackIcon = isTrack2 ? Factory : PackageCheck;
            return (
              <li
                key={item.id}
                className="card flex flex-col justify-between gap-4 !p-5 sm:flex-row sm:items-center"
              >
                <div className="flex min-w-0 gap-4">
                  <span
                    className={`hidden h-11 w-11 shrink-0 items-center justify-center rounded-xl sm:inline-flex ${
                      isTrack2 ? "bg-accent-600 text-white" : "bg-leaf text-white"
                    }`}
                  >
                    <TrackIcon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <div className="min-w-0">
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                          isTrack2
                            ? "border-accent-200 bg-accent-50 text-accent-700"
                            : "border-brand-200 bg-brand-50 text-brand-800"
                        }`}
                      >
                        {isTrack2 ? "Process and System" : "Product Quality"}
                      </span>
                      <span className="font-mono text-xs text-slate-400">
                        #{item.id.slice(0, 8)}
                      </span>
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
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Link
                    href={`/assessment/${item.id}/hub`}
                    className="btn-primary px-4 py-2"
                  >
                    Resume
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleRemove(item.id)}
                    aria-label="Remove saved assessment"
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-coral/40 hover:bg-coral/5 hover:text-coral"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                    Remove
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </PageShell>
  );
}
