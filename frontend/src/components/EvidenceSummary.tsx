import type { RequirementSummary } from "@/types";

function Group({ title, items, tone }: { title: string; items: RequirementSummary[]; tone: string }) {
  return (
    <section className={`rounded-2xl border p-5 ${tone}`}>
      <h3 className="font-bold text-ink">{title} <span className="text-sm font-normal">({items.length})</span></h3>
      {items.length ? (
        <ul className="mt-3 space-y-3">
          {items.map((item) => (
            <li key={item.requirement_id}>
              <p className="font-semibold">{item.title}</p>
              <p className="mt-1 text-sm text-slate-600">{item.rationale}</p>
            </li>
          ))}
        </ul>
      ) : <p className="mt-2 text-sm text-slate-600">None identified from current evidence.</p>}
    </section>
  );
}

export function EvidenceSummary({ strengths, gaps, unknowns }: { strengths: RequirementSummary[]; gaps: RequirementSummary[]; unknowns: RequirementSummary[] }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Group title="Confirmed strengths" items={strengths} tone="border-emerald-200 bg-emerald-50" />
      <Group title="Possible gaps" items={gaps} tone="border-amber-200 bg-amber-50" />
      <Group title="Unknown / not yet verified" items={unknowns} tone="border-slate-200 bg-slate-50" />
    </div>
  );
}
