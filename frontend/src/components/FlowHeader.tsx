import type { ReactNode } from "react";

import { SiteLogo } from "@/components/SiteLogo";

export { FlowSteps } from "@/components/FlowSteps";

interface FlowHeaderProps {
  logoHref?: string;
  trailing?: ReactNode;
  maxWidth?: "3xl" | "4xl" | "5xl";
}

const WIDTH: Record<string, string> = {
  "3xl": "max-w-3xl",
  "4xl": "max-w-4xl",
  "5xl": "max-w-5xl",
};

/** Compact sticky header for in-flow assessment pages. */
export function FlowHeader({ logoHref = "/", trailing, maxWidth = "4xl" }: FlowHeaderProps) {
  const widthClass = WIDTH[maxWidth] ?? WIDTH["4xl"];
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-surface/80 backdrop-blur-md">
      <div className={`mx-auto flex items-center justify-between gap-4 px-4 py-3 sm:px-6 ${widthClass}`}>
        <SiteLogo href={logoHref} />
        {trailing ? <div className="flex items-center gap-2">{trailing}</div> : null}
      </div>
    </header>
  );
}

/** Small monospace assessment id chip. */
export function AssessmentIdChip({ id }: { id: string }) {
  return (
    <span className="rounded-lg bg-slate-100 px-2.5 py-1 font-mono text-xs text-slate-500">
      #{id.slice(0, 8)}
    </span>
  );
}
