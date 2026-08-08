import { AlertCircle, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";

interface Props {
  message: string;
  title?: string;
  onRetry?: () => void;
  action?: ReactNode;
  className?: string;
}

export function ErrorAlert({ message, title, onRetry, action, className = "" }: Props) {
  return (
    <div
      role="alert"
      className={`flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-900 ${className}`}
    >
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-red-100 text-red-600">
        <AlertCircle className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        {title ? <p className="font-semibold">{title}</p> : null}
        <p className={`text-sm leading-relaxed ${title ? "mt-0.5 text-red-800" : ""}`}>{message}</p>
        {(onRetry || action) && (
          <div className="mt-3 flex flex-wrap items-center gap-3">
            {onRetry ? (
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-red-700"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Retry
              </button>
            ) : null}
            {action}
          </div>
        )}
      </div>
    </div>
  );
}
