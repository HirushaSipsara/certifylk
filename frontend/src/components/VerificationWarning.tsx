import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

interface VerificationWarningProps {
  title?: string;
  children?: ReactNode;
  className?: string;
}

/**
 * Reusable warning for draft / unverified (content_verified=false) catalogue content.
 * Presented as an informative caution, never as a fatal system error.
 */
export function VerificationWarning({
  title = "Draft catalogue content",
  children,
  className = "",
}: VerificationWarningProps) {
  return (
    <aside
      className={`flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 sm:p-5 ${className}`}
    >
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
        <AlertTriangle className="h-4 w-4" />
      </span>
      <div className="text-sm leading-relaxed text-amber-900">
        <p className="font-semibold">{title}</p>
        <p className="mt-0.5 text-amber-800">
          {children ??
            "Verify current requirements with the relevant certification authority before making compliance or financial decisions."}
        </p>
      </div>
    </aside>
  );
}
