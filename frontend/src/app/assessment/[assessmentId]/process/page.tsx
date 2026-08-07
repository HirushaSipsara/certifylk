"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { QuestionCard } from "@/components/QuestionCard";
import { api, ApiError } from "@/lib/api";
import type { Assessment, Question, SchemeChip } from "@/types";

export default function ProcessPage() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;
  const router = useRouter();

  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [scheme, setScheme] = useState<SchemeChip | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [steps, setSteps] = useState<string[]>(["", "", "", "", ""]);
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
        setAssessment(a);

        // Pre-fill existing steps if present
        if (a.process_steps && a.process_steps.length > 0) {
          const loadedSteps = a.process_steps.map((s) => s.text);
          while (loadedSteps.length < 5) loadedSteps.push("");
          setSteps(loadedSteps.slice(0, 5));
        }

        // Fetch schemes to find linked scheme
        const schemes = await api.listSchemes();
        const linked = schemes.find((s) => {
          const profileData = a.profile as Record<string, unknown>;
          const appDec = profileData?.applicability_decision as Record<string, unknown> | undefined;
          return appDec?.recommended_path_scheme_id === s.id;
        });
        if (!cancelled && linked) setScheme(linked);

        // Fetch adaptive questions if profile is complete
        try {
          const plan = await api.adaptivePlan(assessmentId);
          if (!cancelled && plan.questions) {
            setQuestions(plan.questions);
          }
        } catch {
          // If adaptive plan is not ready yet, continue with step input
        }
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

  function handleStepChange(index: number, value: string) {
    setSteps((prev) => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  }

  function handleAnswerChange(questionId: string, value: string, otherText?: string) {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { value, ...(otherText ? { other_text: otherText } : {}) },
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Validate at least 3 steps contain text
    const nonEntries = steps.filter((s) => s.trim().length > 0);
    if (nonEntries.length < 3) {
      setError("Please describe at least 3 main steps of your manufacturing process.");
      return;
    }

    setSubmitting(true);
    try {
      // 1. Save process steps & adaptive answers
      const adaptivePayload = Object.entries(answers).map(([qId, val]) => ({
        question_id: qId,
        value: val.value,
        other_text: val.other_text ?? null,
      }));

      await api.saveProcess(assessmentId, {
        steps,
        adaptive_answers: adaptivePayload,
      });

      // 2. Extract structured process stages
      await api.analyzeProcess(assessmentId);

      // 3. Create scheme-bound evidence plan
      await api.evidencePlan(assessmentId);

      // 4. Continue to evidence upload
      router.push(`/assessment/${assessmentId}/evidence`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save process information.");
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-sand">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-500">Loading process form…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-sand">
      {submitting && <LoadingOverlay message="Analyzing manufacturing process & preparing evidence plan…" />}

      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-5 py-4 flex items-center justify-between">
          <Link href={`/assessment/${assessmentId}/hub`} className="flex items-center gap-2 group">
            <span className="text-2xl">🍃</span>
            <span className="font-bold text-emerald-800 text-lg">CertifyLK</span>
          </Link>
          <span className="text-xs font-mono text-slate-400">#{assessmentId.slice(0, 8)}</span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-5 py-10 space-y-8">
        {/* Scheme Context Header */}
        {scheme && (
          <div className="bg-white rounded-2xl border border-emerald-200 p-4 flex items-center justify-between shadow-sm">
            <div>
              <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
                Target Certification Standard
              </span>
              <h2 className="text-base font-bold text-ink">{scheme.name}</h2>
            </div>
            <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2.5 py-1 rounded-full border border-emerald-200">
              {scheme.short_code}
            </span>
          </div>
        )}

        <div>
          <h1 className="text-3xl font-bold text-ink">Production Process</h1>
          <p className="text-sm text-slate-600 mt-1">
            Describe the main steps of your manufacturing process from raw ingredient receiving to finished product storage.
          </p>
        </div>

        {error && <ErrorAlert message={error} />}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Step Inputs */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 space-y-6 shadow-sm">
            <h2 className="text-lg font-bold text-ink border-b border-slate-100 pb-3">
              Manufacturing Steps (5 Steps)
            </h2>
            <p className="text-xs text-slate-500">
              Enter at least 3 sequential production steps (e.g. 1. Receiving fruit, 2. Washing &amp; peeling, 3. Cooking, 4. Bottling, 5. Storage).
            </p>

            <div className="space-y-4">
              {steps.map((stepText, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-800 font-bold text-sm flex items-center justify-center shrink-0">
                    {idx + 1}
                  </span>
                  <input
                    type="text"
                    value={stepText}
                    onChange={(e) => handleStepChange(idx, e.target.value)}
                    placeholder={`Step ${idx + 1} (e.g. ${
                      idx === 0
                        ? "Receiving raw materials"
                        : idx === 1
                        ? "Washing and peeling fruit"
                        : idx === 2
                        ? "Cooking and pasteurization"
                        : idx === 3
                        ? "Hot filling into glass bottles"
                        : "Crate storage & distribution"
                    })`}
                    className="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm text-ink focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Adaptive Questions (if assigned by backend API) */}
          {questions.length > 0 && (
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 space-y-6 shadow-sm">
              <h2 className="text-lg font-bold text-ink border-b border-slate-100 pb-3">
                Process Clarification Questions
              </h2>
              <div className="space-y-6">
                {questions.map((q) => (
                  <QuestionCard
                    key={q.id}
                    question={q}
                    value={answers[q.id]?.value ?? ""}
                    otherText={answers[q.id]?.other_text ?? ""}
                    onChange={(val, oText) => handleAnswerChange(q.id, val, oText)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Submit Action */}
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
              Save &amp; Prepare Evidence Plan →
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
