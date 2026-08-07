import type { RoadmapItem } from "@/types";

import { CostRange } from "./CostRange";

function costTypeBadge(costType?: string) {
  const map: Record<string, { label: string; cls: string }> = {
    certifying_body_fee: { label: "Certification Body Fee", cls: "bg-purple-100 text-purple-800 border-purple-200" },
    lab_testing_fee: { label: "Laboratory Fee", cls: "bg-blue-100 text-blue-800 border-blue-200" },
    business_capex: { label: "Business Capex", cls: "bg-amber-100 text-amber-900 border-amber-200" },
    business_opex: { label: "Business Opex", cls: "bg-emerald-100 text-emerald-900 border-emerald-200" },
  };
  const item = map[costType ?? ""] ?? { label: "Action", cls: "bg-gray-100 text-gray-700 border-gray-200" };
  return (
    <span className={`inline-block text-xs font-semibold px-2.5 py-0.5 rounded-full border ${item.cls}`}>
      {item.label}
    </span>
  );
}

export function RoadmapChecklist({ items }: { items: RoadmapItem[] }) {
  return (
    <section>
      <h2 className="text-2xl font-bold text-ink">Prioritized readiness roadmap</h2>
      <ol className="mt-5 space-y-4">
        {items.map((item, index) => (
          <li key={item.recommendation_id} className="rounded-2xl border border-slate-200 p-5 bg-white shadow-sm">
            <div className="flex items-start gap-4">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ink font-bold text-white text-sm">
                {index + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <h3 className="text-lg font-bold text-ink">{item.title}</h3>
                  {costTypeBadge(item.cost_type)}
                </div>
                <p className="mt-2 text-slate-600 text-sm leading-relaxed">{item.explanation}</p>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {item.implementation_steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ul>
                <div className="mt-4 grid gap-1 sm:grid-cols-2 bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <CostRange label="One-time" range={item.one_time_cost} quoteRequired={item.quote_required} />
                  <CostRange label="Recurring" range={item.recurring_cost} quoteRequired={item.quote_required} />
                </div>
                <p className="mt-3 text-sm font-semibold text-leaf">
                  Expected readiness gain: +{item.expected_gain.toFixed(1)} · projected score after this item: {item.projected_score}/100
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {item.cost_note}
                  {item.effective_date ? ` Effective ${item.effective_date}.` : ""}
                  {item.last_reviewed ? ` Reviewed ${item.last_reviewed}.` : ""}
                </p>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
