import type { ReactNode } from "react";

interface LoadingStateProps {
  message?: string;
  detail?: ReactNode;
  className?: string;
}

export function Spinner({
  className = "",
  size = "h-4 w-4",
}: {
  className?: string;
  size?: string;
}) {
  return (
    <span
      role="status"
      aria-hidden="true"
      className={`inline-block animate-spin rounded-full border-2 border-current border-t-transparent ${size} ${className}`}
    />
  );
}

/** Full-panel loading state with an accessible status region and optional detail copy. */
export function LoadingState({ message = "Loading…", detail, className = "" }: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex flex-col items-center justify-center gap-4 py-16 text-center ${className}`}
    >
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-leaf/10 text-leaf">
        <Spinner size="h-6 w-6" />
      </span>
      <p className="text-sm font-semibold text-ink">{message}</p>
      {detail ? <p className="max-w-xs text-xs leading-relaxed text-slate-500">{detail}</p> : null}
    </div>
  );
}

/** Simple skeleton block for content placeholders. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-slate-200/70 ${className}`} />;
}
