import { Check } from "lucide-react";

interface FlowStepsProps {
  steps: string[];
  current: number; // 1-based index of the active step
  tone?: "leaf" | "navy";
  prefix?: string;
  className?: string;
}

/**
 * Compact numbered step tracker for the top of multi-step flow pages.
 * Labels collapse on small screens, leaving the numbered dots visible.
 */
export function FlowSteps({ steps, current, tone = "leaf", prefix, className = "" }: FlowStepsProps) {
  const activeBg = tone === "navy" ? "bg-navy" : "bg-leaf";
  const activeText = tone === "navy" ? "text-navy" : "text-leaf-dark";

  return (
    <nav aria-label="Progress" className={`flex items-center gap-1.5 text-sm ${className}`}>
      {prefix ? (
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-bold ${
            tone === "navy" ? "bg-navy/10 text-navy" : "bg-leaf/10 text-leaf-dark"
          }`}
        >
          {prefix}
        </span>
      ) : null}
      {steps.map((label, index) => {
        const step = index + 1;
        const done = step < current;
        const active = step === current;
        return (
          <div key={label} className="flex items-center gap-1.5">
            {index > 0 || prefix ? <span className="text-slate-300" aria-hidden="true">/</span> : null}
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                done
                  ? `${activeBg} text-white`
                  : active
                    ? `${activeBg} text-white`
                    : "bg-slate-200 text-slate-400"
              }`}
              aria-current={active ? "step" : undefined}
            >
              {done ? <Check className="h-3.5 w-3.5" /> : step}
            </span>
            <span
              className={`hidden text-xs font-medium sm:inline ${active ? activeText : "text-slate-400"}`}
            >
              {label}
            </span>
          </div>
        );
      })}
    </nav>
  );
}
