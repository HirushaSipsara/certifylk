"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Factory,
  Cog,
  FileText,
  MessagesSquare,
  BarChart3,
  Check,
  ArrowRight,
  Lock,
  Award,
  CalendarClock,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { api, ApiError } from "@/lib/api";
import type { Assessment, SchemeChip } from "@/types";
import { FlowHeader, AssessmentIdChip } from "@/components/FlowHeader";
import { TierBadge } from "@/components/TierBadge";
import { VerificationWarning } from "@/components/VerificationWarning";
import { LoadingState } from "@/components/LoadingState";
import { EmptyState } from "@/components/EmptyState";

const STEPS: { id: string; label: string; description: string; icon: LucideIcon }[] = [
  { id: "profile", label: "Business Profile", description: "Tell us about your operation", icon: Factory },
  { id: "process", label: "Production Process", description: "Map your production steps", icon: Cog },
  { id: "evidence", label: "Evidence Upload", description: "Share supporting documents", icon: FileText },
  { id: "clarification", label: "Clarifications", description: "Answer a few follow-ups", icon: MessagesSquare },
  { id: "result", label: "Readiness Report", description: "Your scored readiness summary", icon: BarChart3 },
];

const PAGE_ORDER = ["profile", "process", "evidence", "clarification", "result"];

function stepIndex(page: string): number {
  return PAGE_ORDER.indexOf(page);
}

export default function AssessmentHubPage() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;

  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [scheme, setScheme] = useState<SchemeChip | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const a = await api.getAssessment(assessmentId);
        if (!cancelled) setAssessment(a);
        const schemes = await api.listSchemes();
        const linked = schemes.find((s) => {
          const profileData = a.profile as Record<string, unknown>;
          const appDec = profileData?.applicability_decision as Record<string, unknown> | undefined;
          return appDec?.recommended_path_scheme_id === s.id;
        });
        if (!cancelled && linked) setScheme(linked);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load assessment.");
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

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <LoadingState message="Loading your assessment…" />
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface p-6">
        <EmptyState
          icon={BarChart3}
          title="Assessment not found"
          description={error ?? "This assessment could not be loaded."}
          action={
            <Link href="/" className="btn-primary">
              Start new assessment
            </Link>
          }
        />
      </div>
    );
  }

  const currentStep = stepIndex(assessment.current_page);
  const isCompleted = assessment.status === "completed";

  return (
    <div className="min-h-screen bg-surface">
      <FlowHeader
        maxWidth="5xl"
        trailing={
          <>
            <span className="hidden sm:block">
              <AssessmentIdChip id={assessmentId} />
            </span>
            {isCompleted && (
              <Link href={`/assessment/${assessmentId}/result`} className="btn-primary px-4 py-2 text-sm">
                View report
              </Link>
            )}
          </>
        }
      />

      <main className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6 sm:py-10">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-leaf">Assessment hub</p>
          <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            Track your readiness progress
          </h1>
          <p className="mt-2 max-w-2xl text-slate-600">
            Work through each step at your own pace. Your answers are saved as you go.
          </p>
        </div>

        {scheme && (
          <div className="card flex flex-col gap-4 p-5 sm:flex-row sm:items-start">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-mist text-leaf">
              <Award className="h-5 w-5" aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <h2 className="text-base font-semibold text-ink">{scheme.name}</h2>
                <TierBadge tier={scheme.mandatory_tier} />
              </div>
              <p className="line-clamp-2 text-sm text-slate-600">{scheme.summary}</p>
              {scheme.typical_timeline_days && (
                <p className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500">
                  <CalendarClock className="h-3.5 w-3.5" aria-hidden="true" />
                  Typical timeline: ~{Math.round(scheme.typical_timeline_days / 30)} months
                </p>
              )}
            </div>
            <Link
              href={`/assessment/${assessmentId}/hub/requirements`}
              className="inline-flex items-center gap-1.5 whitespace-nowrap text-sm font-semibold text-leaf transition-colors hover:text-leaf-dark"
            >
              View requirements
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </div>
        )}

        <section className="card overflow-hidden p-0">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Assessment steps
            </h2>
          </div>
          <ol className="divide-y divide-slate-100">
            {STEPS.map((step, idx) => {
              const done = idx < currentStep || isCompleted;
              const active = idx === currentStep && !isCompleted;
              const locked = idx > currentStep && !isCompleted;
              const StepIcon = step.icon;

              return (
                <li
                  key={step.id}
                  className={`flex items-center gap-4 px-5 py-4 transition-colors ${
                    active ? "bg-mist/60" : done ? "hover:bg-slate-50" : ""
                  }`}
                >
                  <span
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                      done
                        ? "bg-leaf text-white"
                        : active
                          ? "bg-mist text-leaf ring-2 ring-leaf/40"
                          : "bg-slate-100 text-slate-400"
                    }`}
                  >
                    {done ? (
                      <Check className="h-5 w-5" aria-hidden="true" />
                    ) : (
                      <StepIcon className="h-5 w-5" aria-hidden="true" />
                    )}
                  </span>

                  <div className="min-w-0 flex-1">
                    <p
                      className={`text-sm font-semibold ${
                        done ? "text-ink" : active ? "text-ink" : "text-slate-400"
                      }`}
                    >
                      {step.label}
                    </p>
                    <p className={`mt-0.5 text-xs ${active ? "text-leaf" : "text-slate-400"}`}>
                      {active ? "In progress" : step.description}
                    </p>
                  </div>

                  {(active || done) && step.id !== "result" && (
                    <Link
                      href={`/assessment/${assessmentId}/${step.id}`}
                      id={`hub-step-${step.id}`}
                      className={`inline-flex items-center gap-1.5 rounded-xl border px-3.5 py-1.5 text-sm font-semibold transition-colors ${
                        active
                          ? "border-leaf bg-leaf text-white hover:bg-leaf-dark"
                          : "border-slate-200 text-slate-600 hover:border-leaf/40 hover:text-leaf"
                      }`}
                    >
                      {active ? "Continue" : "Review"}
                    </Link>
                  )}
                  {step.id === "result" && (done || isCompleted) && (
                    <Link
                      href={`/assessment/${assessmentId}/result`}
                      id="hub-step-result"
                      className="inline-flex items-center gap-1.5 rounded-xl border border-leaf bg-leaf px-3.5 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-leaf-dark"
                    >
                      View report
                    </Link>
                  )}
                  {locked && (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-300">
                      <Lock className="h-3.5 w-3.5" aria-hidden="true" />
                      Locked
                    </span>
                  )}
                </li>
              );
            })}
          </ol>
        </section>

        <VerificationWarning>
          <strong className="font-semibold">Educational tool only.</strong> CertifyLK is a readiness
          preparation tool, not a certification issuer, auditor, or official inspection body. All requirement
          content referencing SLS standards is approximate and has not been independently verified against the
          purchased SLSI standard text. Consult the Sri Lanka Standards Institution (SLSI) for official
          certification requirements.
        </VerificationWarning>
      </main>
    </div>
  );
}
