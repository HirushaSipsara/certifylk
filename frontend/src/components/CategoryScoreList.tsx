import type { CategoryScore } from "@/types";

export function CategoryScoreList({ scores }: { scores: CategoryScore[] }) {
  return (
    <section>
      <h2 className="text-2xl font-bold text-ink">Readiness by category</h2>
      <div className="mt-4 space-y-4">
        {scores.map((item) => (
          <div key={item.category}>
            <div className="mb-1 flex justify-between gap-4 text-sm font-semibold">
              <span>{item.label}</span><span>{item.score}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full bg-leaf" style={{ width: `${item.score}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
