interface StepIndicatorProps {
  current: number;
  total: number;
  label?: string;
}

export function StepIndicator({ current, total, label }: StepIndicatorProps) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500">
      <div className="flex items-center gap-1.5">
        {Array.from({ length: total }, (_, index) => {
          const step = index + 1;
          const active = step === current;
          const done = step < current;
          return (
            <span
              key={step}
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                active
                  ? "bg-leaf text-white"
                  : done
                    ? "bg-emerald-100 text-leaf"
                    : "bg-slate-100 text-slate-400"
              }`}
            >
              {done ? (
                <svg className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                step
              )}
            </span>
          );
        })}
      </div>
      {label ? (
        <span className="hidden font-medium text-leaf sm:inline">{label}</span>
      ) : (
        <span className="text-xs font-medium sm:hidden">
          Step {current} of {total}
        </span>
      )}
    </div>
  );
}
