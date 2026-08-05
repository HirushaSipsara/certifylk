"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { AssessmentShell } from "@/components/AssessmentShell";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { QuestionCard } from "@/components/QuestionCard";
import { useAssessment } from "@/hooks/useAssessment";
import { api } from "@/lib/api";

export default function ClarificationPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const router = useRouter();
  const { assessment, loading, error: loadError, refresh } = useAssessment(assessmentId);
  const [answers, setAnswers] = useState<Record<string, { value: string; other_text?: string }>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const questions = assessment?.assigned_questions.filter((question) => question.page === "clarification") ?? [];

  async function submit() {
    if (busy) return;
    const incomplete = questions.some((question) => !answers[question.id]?.value || (answers[question.id].value === "other" && !answers[question.id].other_text?.trim()));
    if (incomplete) {
      setError("Answer every clarification question before viewing your result.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.saveClarifications(assessmentId, { answers: questions.map((question) => ({ question_id: question.id, ...answers[question.id] })) });
      await api.complete(assessmentId);
      router.push(`/assessment/${assessmentId}/result`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not complete the assessment.");
      setBusy(false);
    }
  }

  if (loading) return <LoadingOverlay message="Loading final clarification questions…" />;

  return (
    <AssessmentShell currentStep={4} title="A few final clarifications" description="These three to five approved questions focus on high-priority details that your earlier answers and evidence did not resolve.">
      {busy ? <LoadingOverlay message="Calculating your readiness score, costs and roadmap…" /> : null}
      {loadError ? <ErrorAlert message={loadError} onRetry={() => void refresh()} /> : null}
      {error ? <div className="mb-5"><ErrorAlert message={error} /></div> : null}
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
      <button type="button" onClick={() => void submit()} disabled={busy || Boolean(loadError) || questions.length < 3} className="mt-6 w-full rounded-xl bg-leaf px-6 py-3 font-bold text-white hover:bg-ink disabled:opacity-50">Calculate my readiness roadmap</button>
    </AssessmentShell>
  );
}
