"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AssessmentShell } from "@/components/AssessmentShell";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { ProcessStepList, type ProcessFormValues } from "@/components/ProcessStepList";
import { QuestionCard } from "@/components/QuestionCard";
import { useAssessment } from "@/hooks/useAssessment";
import { api } from "@/lib/api";

const processSchema = z.object({
  steps: z
    .tuple([z.string(), z.string(), z.string(), z.string(), z.string()])
    .refine((steps) => steps.filter((step) => step.trim()).length >= 3, {
      message: "Enter at least three production steps.",
    }),
});

export default function ProcessPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const router = useRouter();
  const { assessment, loading, error: loadError, refresh } = useAssessment(assessmentId);
  const [answers, setAnswers] = useState<Record<string, { value: string; other_text?: string }>>({});
  const [questionError, setQuestionError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ProcessFormValues>({
    resolver: zodResolver(processSchema),
    defaultValues: { steps: ["", "", "", "", ""] },
  });

  useEffect(() => {
    if (assessment?.process_steps.length) {
      const steps: [string, string, string, string, string] = ["", "", "", "", ""];
      assessment.process_steps.forEach((step) => { steps[step.position - 1] = step.text; });
      reset({ steps });
    }
  }, [assessment, reset]);

  const questions = assessment?.assigned_questions.filter((question) => question.page === "adaptive") ?? [];

  async function submit(values: ProcessFormValues) {
    if (busy) return;
    const missing = questions.filter((question) => !answers[question.id]?.value || (answers[question.id].value === "other" && !answers[question.id].other_text?.trim()));
    if (missing.length) {
      setQuestionError("Answer every adaptive question before continuing.");
      return;
    }
    setBusy(true);
    setError(null);
    setQuestionError(null);
    try {
      await api.saveProcess(assessmentId, {
        steps: values.steps,
        adaptive_answers: questions.map((question) => ({ question_id: question.id, ...answers[question.id] })),
      });
      await api.analyzeProcess(assessmentId);
      await api.evidencePlan(assessmentId);
      router.push(`/assessment/${assessmentId}/evidence`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not analyze your process.");
      setBusy(false);
    }
  }

  if (loading) return <LoadingOverlay message="Loading your process questions…" />;

  return (
    <AssessmentShell currentStep={2} title="Describe your manufacturing process" description="Enter your five main steps in order. At least three are required. The extra questions were selected only from our approved bank.">
      {busy ? <LoadingOverlay message="Extracting your process and planning relevant evidence…" /> : null}
      {loadError ? <ErrorAlert message={loadError} onRetry={() => void refresh()} /> : null}
      {error ? <div className="mb-5"><ErrorAlert message={error} /></div> : null}
      <form onSubmit={handleSubmit(submit)} className="space-y-8">
        <section>
          <h2 className="mb-4 text-lg font-bold text-ink">Your five main production steps</h2>
          <ProcessStepList register={register} errors={errors} />
          {errors.steps?.root?.message ? <p className="mt-2 text-sm text-coral">{errors.steps.root.message}</p> : null}
          {typeof errors.steps?.message === "string" ? <p className="mt-2 text-sm text-coral">{errors.steps.message}</p> : null}
        </section>
        <section>
          <h2 className="mb-4 text-lg font-bold text-ink">A few relevant questions</h2>
          <div className="space-y-4">
            {questions.map((question) => (
              <QuestionCard
                key={question.id}
                question={question}
                value={answers[question.id]?.value}
                otherText={answers[question.id]?.other_text}
                onChange={(value) => setAnswers((current) => ({ ...current, [question.id]: { ...current[question.id], value } }))}
                onOtherChange={(other_text) => setAnswers((current) => ({ ...current, [question.id]: { value: current[question.id]?.value ?? "other", other_text } }))}
              />
            ))}
          </div>
          {questionError ? <p role="alert" className="mt-3 text-sm text-coral">{questionError}</p> : null}
        </section>
        <button type="submit" disabled={busy || Boolean(loadError) || questions.length < 2} className="w-full rounded-xl bg-leaf px-6 py-3 font-bold text-white hover:bg-ink disabled:opacity-50">Continue to evidence</button>
      </form>
    </AssessmentShell>
  );
}
