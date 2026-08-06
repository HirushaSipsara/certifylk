import type { AIExecutionMetadata } from "@/types";

interface Props extends AIExecutionMetadata {
  className?: string;
}

export function AIAnalysisStatus({ provider, fallback_used, className = "" }: Props) {
  let label: string | null = null;
  let tone = "border-slate-200 bg-slate-50 text-slate-700";

  if (fallback_used === true) {
    label = "Completed using fallback analysis";
    tone = "border-amber-200 bg-amber-50 text-amber-900";
  } else if (provider === "gemini") {
    label = "Analyzed by Gemini";
    tone = "border-emerald-200 bg-emerald-50 text-emerald-900";
  } else if (
    provider === "mock" &&
    (process.env.NODE_ENV !== "production" ||
      process.env.NEXT_PUBLIC_SHOW_MOCK_AI_STATUS === "true")
  ) {
    label = "Analyzed by Mock AI";
  }

  if (!label) return null;

  return (
    <p
      aria-label="AI analysis provider"
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${tone} ${className}`}
    >
      {label}
    </p>
  );
}
