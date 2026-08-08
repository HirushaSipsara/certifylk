"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import { ErrorAlert } from "@/components/ErrorAlert";
import { FlowHeader, AssessmentIdChip } from "@/components/FlowHeader";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { LoadingState } from "@/components/LoadingState";
import { ProcessStepList, type ProcessFormValues } from "@/components/ProcessStepList";
import { QuestionCard } from "@/components/QuestionCard";
import { api, ApiError } from "@/lib/api";
import type { Question, SchemeChip } from "@/types";

export default function ProcessPage() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;
  const router = useRouter();

  const [scheme, setScheme] = useState<SchemeChip | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, { value: string; other_text?: string }>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ProcessFormValues>({
    defaultValues: {
      steps: ["", "", "", "", ""],
    },
  });

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const a = await api.getAssessment(assessmentId);
        if (cancelled) return;

        // Pre-fill existing steps if already saved
        if (a.process?.steps && a.process.steps.length >= 3) {
          const prefill = [...a.process.steps];
          while (prefill.length < 5) prefill.push("");
          setValue("steps", prefill.slice(0, 5) as [string, string, string, string, string]);
        }

        // Fetch linked scheme
        const schemes = await api.listSchemes();
        const linked = schemes.find((s) => {
          const profileData = a.profile as Record<string, unknown>;
          const appDec = profileData?.applicability_decision as Record<string, unknown> | undefined;
          return appDec?.recommended_path_scheme_id === s.id;
        });
        if (!cancelled && linked) setScheme(linked);

        // Fetch adaptive questions
        try {
          const plan = await api.adaptivePlan(assessmentId);
          if (!cancelled && plan.questions) {
            setQuestions(plan.questions);
          }
        } catch {
          // If adaptive plan already fetched, fallback to assigned questions if present
          if (a.assigned_questions && a.assigned_questions.length > 0) {
            setQuestions(a.assigned_questions);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load production process step.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [assessmentId, setValue]);

  function handleAnswerChange(questionId: string, value: string, otherText?: string) {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { value, ...(otherText ? { other_text: otherText } : {}) },
    }));
  }

  async function onSubmit(formValues: ProcessFormValues) {
    setError(null);
    const validSteps = formValues.steps.map((s) => s.trim()).filter(Boolean);
    if (validSteps.length < 3) {
      setError("Please describe at least 3 main production steps in your manufacturing process.");
      return;
    }

    setSubmitting(true);
    try {
      const adaptiveAnswers = Object.entries(answers).map(([qId, val]) => ({
        question_id: qId,
        value: val.value,
        other_text: val.other_text ?? null,
      }));

      await api.saveProcess(assessmentId, {
        steps: validSteps,
        adaptive_answers: adaptiveAnswers,
      });

      await api.analyzeProcess(assessmentId);
      router.push(`/assessment/${assessmentId}/evidence`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save production process.");
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <LoadingState message="Loading process step questions…" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface">
      {submitting && (
        <LoadingOverlay message="Analyzing manufacturing process steps & preparing evidence requirements…" />
      )}
      <FlowHeader
        maxWidth="4xl"
        trailing={<AssessmentIdChip id={assessmentId} />}
      />

      <main className="max-w-3xl mx-auto px-5 py-10 space-y-8">
        <div>
          <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider bg-emerald-100 px-3 py-1 rounded-full">
            Stage 2 of 5 · Production Process
          </span>
          <h1 className="text-3xl font-bold text-ink mt-3">Manufacturing &amp; Process Steps</h1>
          {scheme && <p className="text-xs text-emerald-700 font-medium mt-1">Scheme: {scheme.name}</p>}
          <p className="text-sm text-slate-600 mt-1">
            Describe your step-by-step production flow from raw materials receipt to final packaging and storage.
          </p>
        </div>

        {error && <ErrorAlert message={error} />}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
          {/* Production Steps */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 space-y-6 shadow-sm">
            <div>
              <h2 className="text-lg font-bold text-ink">Ordered Production Steps</h2>
              <p className="text-xs text-slate-500 mt-1">
                List at least 3 sequential manufacturing operations (e.g. ingredient receiving, boiling/mixing, hot filling, sealing, storage).
              </p>
            </div>

            <ProcessStepList register={register} errors={errors} />
          </div>

          {/* Adaptive Questions if any */}
          {questions.length > 0 && (
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 space-y-6 shadow-sm">
              <div>
                <h2 className="text-lg font-bold text-ink">Adaptive Process Questions ({questions.length})</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Tailored questions to assess hygiene and process controls specific to your operations.
                </p>
              </div>

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
          )}

          <div className="flex items-center justify-between pt-4">
            <Link
              href={`/assessment/${assessmentId}/hub`}
              className="text-sm text-slate-500 hover:text-slate-800"
            >
              ← Back to Hub
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="bg-leaf text-white font-bold px-8 py-4 rounded-2xl hover:bg-ink transition-colors disabled:opacity-50 text-sm shadow-card"
            >
              Continue to Evidence Upload →
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
