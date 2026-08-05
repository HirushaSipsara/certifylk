import type { RoadmapItem } from "@/types";

import { CostRange } from "./CostRange";

export function RoadmapChecklist({ items }: { items: RoadmapItem[] }) {
  return (
    <section>
      <h2 className="text-2xl font-bold text-ink">Prioritized readiness roadmap</h2>
      <ol className="mt-5 space-y-4">
        {items.map((item, index) => (
          <li key={item.recommendation_id} className="rounded-2xl border border-slate-200 p-5">
            <div className="flex items-start gap-4">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ink font-bold text-white">{index + 1}</span>
              <div className="min-w-0">
                <h3 className="text-lg font-bold text-ink">{item.title}</h3>
                <p className="mt-2 text-slate-600">{item.explanation}</p>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {item.implementation_steps.map((step) => <li key={step}>{step}</li>)}
                </ul>
                <div className="mt-4 grid gap-1 sm:grid-cols-2">
                  <CostRange label="One-time" range={item.one_time_cost} />
                  <CostRange label="Recurring" range={item.recurring_cost} />
                </div>
                <p className="mt-3 text-sm font-semibold text-leaf">Expected readiness gain: +{item.expected_gain.toFixed(1)} · projected score after this item: {item.projected_score}/100</p>
                <p className="mt-1 text-xs text-slate-500">{item.cost_note} Reviewed {item.last_reviewed}.</p>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
