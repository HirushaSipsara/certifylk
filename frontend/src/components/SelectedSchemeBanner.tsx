import { ShieldCheck } from "lucide-react";

import type { SchemeChip } from "@/types";

interface Props {
  scheme: SchemeChip;
  /** Extra label to prefix, e.g. "Target Certificate" or "Selected Certification" */
  label?: string;
}

/**
 * A persistent, prominent banner displayed across all assessment stage pages to remind
 * the user which certification scheme they are being assessed against.
 */
export function SelectedSchemeBanner({ scheme, label = "Target Certificate" }: Props) {
  return (
    <div
      className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3"
      aria-label={`Selected certification: ${scheme.name}`}
    >
      <ShieldCheck className="h-5 w-5 flex-shrink-0 text-emerald-600" aria-hidden="true" />
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-widest text-emerald-700">
          {label}
        </p>
        <p className="truncate text-sm font-bold text-emerald-900">{scheme.name}</p>
        <p className="text-xs text-emerald-600">
          {scheme.short_code}
          {scheme.body_name ? ` · ${scheme.body_name}` : ""}
        </p>
      </div>
    </div>
  );
}

