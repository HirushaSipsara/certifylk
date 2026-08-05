interface Props {
  score: number;
  completeness: number;
}

export function ReadinessScoreCard({ score, completeness }: Props) {
  return (
    <section className="grid gap-4 sm:grid-cols-2" aria-label="Assessment score summary">
      <div className="rounded-2xl bg-ink p-6 text-white">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime">Readiness score</p>
        <p className="mt-2 text-5xl font-bold">{score}<span className="text-2xl">/100</span></p>
        <p className="mt-3 text-sm text-emerald-50">Preparation readiness, calculated from deterministic requirements.</p>
      </div>
      <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-6 text-ink">
        <p className="text-sm font-semibold uppercase tracking-wider text-leaf">Evidence completeness</p>
        <p className="mt-2 text-5xl font-bold">{completeness}%</p>
        <p className="mt-3 text-sm">How many applicable requirements have confirmed or partial evidence. This is separate from readiness.</p>
      </div>
    </section>
  );
}
