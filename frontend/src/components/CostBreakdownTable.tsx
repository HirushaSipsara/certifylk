"use client";

import type { CostTypeBreakdown } from "@/types";

interface Props {
  summary: {
    one_time_min: number;
    one_time_max: number;
    recurring_min: number;
    recurring_max: number;
    currency: string;
    by_type?: Record<string, CostTypeBreakdown>;
  };
}

const COST_TYPES = [
  { key: "certifying_body_fee", label: "Certification Body Fee", icon: "🏛️", desc: "Application, audit, sampling, and registration fees (e.g. SLSI/CAA)" },
  { key: "lab_testing_fee", label: "Laboratory Testing Fee", icon: "🧪", desc: "Microbiological, chemical, and physical laboratory testing fees" },
  { key: "business_capex", label: "Business Capex", icon: "🏗️", desc: "Infrastructure improvements, equipment, and facility upgrades" },
  { key: "business_opex", label: "Business Opex", icon: "📋", desc: "Operating expenses, pest control contracts, calibration, training" },
] as const;

export function CostBreakdownTable({ summary }: Props) {
  const byType = summary.by_type;

  return (
    <div className="space-y-6">
      {/* Overall Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total One-Time Min
          </span>
          <p className="text-xl font-bold text-ink mt-1">
            Rs. {summary.one_time_min.toLocaleString()}
          </p>
        </div>
        <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total One-Time Max
          </span>
          <p className="text-xl font-bold text-ink mt-1">
            Rs. {summary.one_time_max.toLocaleString()}
          </p>
        </div>
        <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Recurring Min / Year
          </span>
          <p className="text-xl font-bold text-ink mt-1">
            Rs. {summary.recurring_min.toLocaleString()}
          </p>
        </div>
        <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Recurring Max / Year
          </span>
          <p className="text-xl font-bold text-ink mt-1">
            Rs. {summary.recurring_max.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Categorized Breakdown Table */}
      {byType && (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200">
              <tr>
                <th scope="col" className="px-6 py-3.5 font-bold">Cost Category</th>
                <th scope="col" className="px-4 py-3.5 font-bold">Items</th>
                <th scope="col" className="px-4 py-3.5 font-bold">One-Time Range (LKR)</th>
                <th scope="col" className="px-4 py-3.5 font-bold">Recurring Range / Yr (LKR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {COST_TYPES.map((type) => {
                const data = byType[type.key];
                const count = data?.items_count ?? 0;
                const otMin = data?.one_time_min ?? 0;
                const otMax = data?.one_time_max ?? 0;
                const recMin = data?.recurring_min ?? 0;
                const recMax = data?.recurring_max ?? 0;
                const isZero = count === 0 || (otMin === 0 && otMax === 0 && recMin === 0 && recMax === 0);

                return (
                  <tr key={type.key} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{type.icon}</span>
                        <div>
                          <p className="font-bold text-ink text-sm">{type.label}</p>
                          <p className="text-xs text-slate-400">{type.desc}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4 font-mono text-xs font-semibold text-slate-600">
                      {count} {count === 1 ? "action" : "actions"}
                    </td>
                    <td className="px-4 py-4 font-medium text-slate-900">
                      {isZero ? (
                        <span className="text-xs text-slate-400 font-normal">Quote required / Included</span>
                      ) : (
                        `Rs. ${otMin.toLocaleString()} – ${otMax.toLocaleString()}`
                      )}
                    </td>
                    <td className="px-4 py-4 font-medium text-slate-900">
                      {recMin === 0 && recMax === 0 ? (
                        <span className="text-xs text-slate-400 font-normal">None</span>
                      ) : (
                        `Rs. ${recMin.toLocaleString()} – ${recMax.toLocaleString()}`
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
