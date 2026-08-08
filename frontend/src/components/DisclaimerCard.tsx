import { Info } from "lucide-react";

export function DisclaimerCard({
  text,
  className = "",
}: {
  text?: string;
  className?: string;
}) {
  return (
    <aside
      className={`flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-5 text-sm leading-6 text-slate-700 shadow-soft ${className}`}
    >
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-mist text-leaf">
        <Info className="h-4 w-4" />
      </span>
      <div>
        <p className="font-semibold text-ink">Readiness guidance, not certification</p>
        <p className="mt-1 text-slate-600">
          {text ??
            "CertifyLK does not issue, guarantee, or replace SLS certification or an official inspection."}
        </p>
      </div>
    </aside>
  );
}
