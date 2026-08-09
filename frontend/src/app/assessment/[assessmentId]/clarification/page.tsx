"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { LoadingState } from "@/components/LoadingState";
import { FlowHeader, AssessmentIdChip } from "@/components/FlowHeader";
import { QuestionCard } from "@/components/QuestionCard";
import { api, ApiError } from "@/lib/api";
import { SelectedSchemeBanner } from "@/components/SelectedSchemeBanner";
import type { Question, SchemeChip } from "@/types";

export default function ClarificationPage() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;
  const router = useRouter();

  const [scheme, setScheme] = useState<SchemeChip | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, { value: string; other_text?: string }>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const a = await api.getAssessment(assessmentId);
        if (cancelled) return;

        // Fetch linked scheme
        const schemes = await api.listSchemes();
        const linked = schemes.find((s) => {
          const profileData = a.profile as Record<string, unknown>;
          const appDec = profileData?.applicability_decision as Record<string, unknown> | undefined;
          return appDec?.recommended_path_scheme_id === s.id;
        });
        if (!cancelled && linked) setScheme(linked);

        // Load clarification questions
        try {
          const plan = await api.clarificationPlan(assessmentId);
          if (!cancelled && plan.questions) {
            setQuestions(plan.questions);
            if (plan.questions.length === 0) {
              // No clarification questions required — advance directly to complete
              await api.complete(assessmentId);
              router.push(`/assessment/${assessmentId}/result`);
              return;
            }
          }
        } catch {
          // If already in clarification_pending or assigned questions exist
          if (a.assigned_questions && a.assigned_questions.length > 0) {
            setQuestions(a.assigned_questions);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load clarification questions.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [assessmentId, router]);

  function handleAnswerChange(questionId: string, value: string, otherText?: string) {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { value, ...(otherText ? { other_text: otherText } : {}) },
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Verify all assigned questions have answers
    const missing = questions.filter((q) => !answers[q.id]?.value);
    if (missing.length > 0) {
      setError("Please answer all clarification questions before generating your readiness report.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = Object.entries(answers).map(([qId, val]) => ({
        question_id: qId,
        value: val.value,
        other_text: val.other_text ?? null,
      }));

      await api.saveClarifications(assessmentId, { answers: payload });
      await api.complete(assessmentId);
      router.push(`/assessment/${assessmentId}/result`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to submit clarifications.");
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <LoadingState message="Preparing clarification questions…" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface">
      {submitting && <LoadingOverlay message="Executing deterministic evaluation & creating cost-aware roadmap…" />}
      <FlowHeader
        maxWidth="4xl"
        trailing={<AssessmentIdChip id={assessmentId} />}
      />

      <main className="max-w-3xl mx-auto px-5 py-10 space-y-8">
        <div>
          <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider bg-emerald-100 px-3 py-1 rounded-full">
            Stage 4 of 5 · Clarifications
          </span>
          <h1 className="text-3xl font-bold text-ink mt-3">Final Clarifications</h1>
          <p className="text-sm text-slate-600 mt-1">
            Answer these specific questions to resolve remaining requirement uncertainties for your selected certification scheme.
          </p>
          {scheme && <SelectedSchemeBanner scheme={scheme} label="Assessing Against" />}
        </div>

        {error && <ErrorAlert message={error} />}

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 space-y-6 shadow-sm">
            <h2 className="text-lg font-bold text-ink border-b border-slate-100 pb-3">
              Assigned Scheme Questions ({questions.length})
            </h2>

            <div className="space-y-6">
              {questions.map((q) => (
                <QuestionCard
                  key={q.id}
                  question={q}
                  value={answers[q.id]?.value ?? ""}
                  otherText={answers[q.id]?.other_text ?? ""}
                  onChange={(val) => handleAnswerChange(q.id, val)}
                  onOtherChange={(oText) => handleAnswerChange(q.id, "other", oText)}
                />
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-4">
            <Link href={`/assessment/${assessmentId}/evidence`} className="text-sm text-slate-500 hover:text-slate-800">
              ← Back to Evidence
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="bg-leaf text-white font-bold px-8 py-4 rounded-2xl hover:bg-ink transition-colors disabled:opacity-50 text-sm shadow-card"
            >
              Generate Readiness Report →
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
