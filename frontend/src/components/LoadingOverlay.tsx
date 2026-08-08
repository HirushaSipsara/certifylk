import { Spinner } from "./LoadingState";

interface Props {
  message?: string;
  detail?: string;
}

export function LoadingOverlay({ message = "Working on your assessment…", detail }: Props) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-50 grid place-items-center bg-ink/50 p-6 backdrop-blur-sm"
    >
      <div className="w-full max-w-sm rounded-3xl bg-white px-7 py-8 text-center shadow-card-hover animate-fade-in-up">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-leaf/10 text-leaf">
          <Spinner className="h-6 w-6" />
        </span>
        <p className="mt-4 font-semibold text-ink">{message}</p>
        {detail ? <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{detail}</p> : null}
      </div>
    </div>
  );
}
