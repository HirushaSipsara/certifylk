interface Props {
  message?: string;
}

export function LoadingOverlay({ message = "Working on your assessment…" }: Props) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-50 grid place-items-center bg-ink/45 p-6"
    >
      <div className="rounded-2xl bg-white px-7 py-6 text-center shadow-card">
        <div className="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-emerald-100 border-t-leaf" />
        <p className="mt-4 font-semibold text-ink">{message}</p>
      </div>
    </div>
  );
}
