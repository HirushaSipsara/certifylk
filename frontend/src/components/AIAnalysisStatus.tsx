import { Sparkles, ShieldAlert, Cpu } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { AIExecutionMetadata } from "@/types";

interface Props extends Omit<AIExecutionMetadata, "provider"> {
  provider?: string | null;
  className?: string;
}

export function AIAnalysisStatus({ provider, fallback_used, className = "" }: Props) {
  let label: string | null = null;
  let tone = "border-slate-200 bg-slate-50 text-slate-700";
  let Icon: LucideIcon = Cpu;

  if (fallback_used === true) {
    label = "Completed using fallback analysis";
    tone = "border-amber-200 bg-amber-50 text-amber-900";
    Icon = ShieldAlert;
  } else if (provider === "gemini") {
    label = "Analyzed by Gemini";
    tone = "border-emerald-200 bg-emerald-50 text-emerald-900";
    Icon = Sparkles;
  } else if (
    provider === "mock" &&
    (process.env.NODE_ENV !== "production" ||
      process.env.NEXT_PUBLIC_SHOW_MOCK_AI_STATUS === "true")
  ) {
    label = "Analyzed by Mock AI";
    Icon = Cpu;
  }

  if (!label) return null;

  return (
    <span
      aria-label="AI analysis provider"
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${tone} ${className}`}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {label}
    </span>
  );
}
