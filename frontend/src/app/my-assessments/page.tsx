"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { ErrorAlert } from "@/components/ErrorAlert";
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
            href="/education"
            className="text-sm font-medium text-slate-600 hover:text-emerald-700 transition-colors"
          >
            📖 Understand Certification
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 py-10 space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-ink">My Assessments</h1>
          <p className="text-sm text-slate-600 mt-1">
            Browser-local guest assessment recovery. Assessments started on this browser are remembered below.
          </p>
        </div>

        {/* Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 text-xs text-blue-900 leading-relaxed">
          🔒 <strong>Saved on this browser:</strong> CertifyLK guest assessments do not require an account or login. Your saved assessment IDs are stored locally in your browser&apos;s local storage.
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500">Loading saved assessments…</div>
        ) : assessments.length === 0 ? (
          <div className="bg-white rounded-3xl border border-slate-200 p-10 text-center">
            <div className="text-4xl mb-3">📋</div>
            <h2 className="text-lg font-bold text-ink mb-2">No saved assessments found</h2>
            <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
              You haven&apos;t started any readiness assessments on this browser yet. Select a track on the home page to begin.
            </p>
            <Link
              href="/"
              className="inline-block bg-leaf text-white px-6 py-3 rounded-2xl font-bold text-sm hover:bg-ink transition-colors"
            >
              Start New Assessment →
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {assessments.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${
                        item.track === "process_management"
                          ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                          : "bg-emerald-50 text-emerald-800 border-emerald-200"
                      }`}
                    >
                      {item.track === "process_management" ? "Process & System" : "Product Quality"}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">#{item.id.slice(0, 8)}</span>
                  </div>
                  <h3 className="text-base font-bold text-ink">
                    {item.schemeName ?? item.productName ?? "Readiness Assessment"}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Last accessed: {new Date(item.lastSeenAt).toLocaleDateString()} at{" "}
                    {new Date(item.lastSeenAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <Link
                    href={`/assessment/${item.id}/hub`}
                    className="bg-leaf text-white px-4 py-2 rounded-xl text-sm font-bold hover:bg-ink transition-colors"
                  >
                    Resume →
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleRemove(item.id)}
                    className="text-xs text-red-600 hover:text-red-800 border border-red-200 hover:border-red-300 px-3 py-2 rounded-xl transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
