interface Props {
  score: number;
  completeness: number;
}

export function ReadinessScoreCard({ score, completeness }: Props) {
  return (
    <section className="space-y-4" aria-label="Assessment score summary">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl bg-ink p-6 text-white">
          <p className="text-sm font-semibold uppercase tracking-wider text-lime">Readiness score</p>
          <p className="mt-2 text-5xl font-bold">{score}<span className="text-2xl">/100</span></p>
          <p className="mt-3 text-sm text-emerald-50">Readiness reflects your assessment responses and available supporting evidence.</p>
        </div>
        <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-6 text-ink">
          <p className="text-sm font-semibold uppercase tracking-wider text-leaf">Evidence completeness</p>
          <p className="mt-2 text-5xl font-bold">{completeness}%</p>
          <p className="mt-3 text-sm">Evidence completeness reflects how much readiness is supported by accepted uploaded evidence. This is separate from readiness.</p>
        </div>
      </div>
      {completeness === 0 && (
        <p className="rounded-2xl border border-sky-200 bg-sky-50 px-5 py-4 text-sm leading-6 text-slate-700">
          No accepted supporting evidence is currently counted, so evidence completeness is 0%. Your readiness score may still reflect self-reported business, process, and current-state answers.
        </p>
      )}
    </section>
  );
}
