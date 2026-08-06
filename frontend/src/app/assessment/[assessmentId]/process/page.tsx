"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AIAnalysisStatus } from "@/components/AIAnalysisStatus";
import { AssessmentShell } from "@/components/AssessmentShell";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { ProcessStepList, type ProcessFormValues } from "@/components/ProcessStepList";
import { QuestionCard } from "@/components/QuestionCard";
import { useAssessment } from "@/hooks/useAssessment";
import { useLongRunningAnalysis } from "@/hooks/useLongRunningAnalysis";
import { api } from "@/lib/api";
import type { ProcessAnalysisResponse } from "@/types";

const processSchema = z.object({
  steps: z
    .tuple([z.string(), z.string(), z.string(), z.string(), z.string()])
    .refine((steps) => steps.filter((step) => step.trim()).length >= 3, {
      message: "Enter at least three production steps.",
    }),
});

type BusyPhase = "analyzing" | "planning" | null;

export default function ProcessPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const router = useRouter();
  const { assessment, loading, error: loadError, refresh } = useAssessment(assessmentId);
  const [answers, setAnswers] = useState<Record<string, { value: string; other_text?: string }>>({});
  const [questionError, setQuestionError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processSaved, setProcessSaved] = useState(false);
  const [analysis, setAnalysis] = useState<ProcessAnalysisResponse | null>(null);
  const [busyPhase, setBusyPhase] = useState<BusyPhase>(null);
  const takingLonger = useLongRunningAnalysis(busyPhase === "analyzing");
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ProcessFormValues>({
    resolver: zodResolver(processSchema),
    defaultValues: { steps: ["", "", "", "", ""] },
  });

  useEffect(() => {
    if (!assessment) return;
    if (assessment.process_steps.length) {
      const steps: [string, string, string, string, string] = ["", "", "", "", ""];
      assessment.process_steps.forEach((step) => { steps[step.position - 1] = step.text; });
      reset({ steps });
    }
    if (assessment.status === "process_complete") setProcessSaved(true);
  }, [assessment, reset]);

  const questions = assessment?.assigned_questions.filter((question) => question.page === "adaptive") ?? [];

  async function analyzeSavedProcess() {
    if (busyPhase) return;
    setBusyPhase("analyzing");
    setError(null);
    try {
      setAnalysis(await api.analyzeProcess(assessmentId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not analyze your process.");
    } finally {
      setBusyPhase(null);
    }
  }

  async function submit(values: ProcessFormValues) {
    if (busyPhase) return;
    const missing = questions.filter((question) => !answers[question.id]?.value || (answers[question.id].value === "other" && !answers[question.id].other_text?.trim()));
    if (missing.length) {
      setQuestionError("Answer every adaptive question before continuing.");
      return;
    }
    setBusyPhase("analyzing");
    setError(null);
    setQuestionError(null);
    try {
      await api.saveProcess(assessmentId, {
        steps: values.steps,
        adaptive_answers: questions.map((question) => ({ question_id: question.id, ...answers[question.id] })),
      });
      setProcessSaved(true);
      setAnalysis(await api.analyzeProcess(assessmentId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not analyze your process.");
    } finally {
      setBusyPhase(null);
    }
  }

  async function continueToEvidence() {
    if (busyPhase) return;
    setBusyPhase("planning");
    setError(null);
    try {
      await api.evidencePlan(assessmentId);
      router.push(`/assessment/${assessmentId}/evidence`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not prepare the evidence requests.");
      setBusyPhase(null);
    }
  }

  if (loading) return <LoadingOverlay message="Loading your process questions…" />;

  return (
    <AssessmentShell currentStep={2} title="Describe your manufacturing process" description="Enter your five main steps in order. At least three are required. The extra questions were selected only from our approved bank.">
      {busyPhase ? (
        <LoadingOverlay
          message={busyPhase === "planning" ? "Preparing relevant evidence requests…" : takingLonger ? "Analysis is taking longer than expected" : "Analyzing manufacturing process"}
        />
      ) : null}
      {loadError ? <ErrorAlert message={loadError} onRetry={() => void refresh()} /> : null}
      {error ? (
        <div className="mb-5">
          <ErrorAlert
            message={error}
            onRetry={processSaved ? () => void (analysis ? continueToEvidence() : analyzeSavedProcess()) : undefined}
          />
        </div>
      ) : null}

      {analysis ? (
        <section aria-labelledby="process-review-title" className="space-y-5">
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
            <h2 id="process-review-title" className="text-xl font-bold text-ink">Process analysis complete</h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">Review how your steps were structured before moving to evidence collection.</p>
            <AIAnalysisStatus provider={analysis.provider} fallback_used={analysis.fallback_used} className="mt-3" />
          </div>
          <ol className="space-y-3">
            {analysis.stages.map((stage) => (
              <li key={stage.position} className="rounded-xl border border-slate-200 p-4">
                <p className="font-semibold text-ink">{stage.position}. {stage.name}</p>
                <p className="mt-1 text-sm text-slate-600">Tags: {stage.tags.join(", ")}</p>
              </li>
            ))}
          </ol>
          {analysis.uncertainties.length ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <h3 className="font-bold text-ink">Details to confirm later</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                {analysis.uncertainties.map((uncertainty) => <li key={uncertainty}>{uncertainty}</li>)}
              </ul>
            </div>
          ) : null}
          <button type="button" onClick={() => void continueToEvidence()} disabled={Boolean(busyPhase)} className="w-full rounded-xl bg-leaf px-6 py-3 font-bold text-white hover:bg-ink disabled:opacity-50">Continue to evidence</button>
        </section>
      ) : processSaved ? (
        <section className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <h2 className="text-lg font-bold text-ink">Your process steps are saved</h2>
          <p className="mt-2 text-sm leading-6 text-slate-700">Run the analysis to review the structured stages and the provider used.</p>
          <button type="button" onClick={() => void analyzeSavedProcess()} disabled={Boolean(busyPhase)} className="mt-4 w-full rounded-xl bg-leaf px-6 py-3 font-bold text-white hover:bg-ink disabled:opacity-50">Analyze saved process</button>
        </section>
      ) : (
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
          <button type="submit" disabled={Boolean(busyPhase) || Boolean(loadError) || questions.length < 2} className="w-full rounded-xl bg-leaf px-6 py-3 font-bold text-white hover:bg-ink disabled:opacity-50">Analyze process</button>
        </form>
      )}
    </AssessmentShell>
  );
}
