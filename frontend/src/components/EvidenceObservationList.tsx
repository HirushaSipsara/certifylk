import type { EvidenceObservation } from "@/types";
import { AIAnalysisStatus } from "@/components/AIAnalysisStatus";

const presentations = {
  supports: {
    label: "Supports",
    icon: "✓",
    tone: "border-emerald-200 bg-emerald-50",
    badge: "bg-emerald-100 text-emerald-900",
  },
  concern: {
    label: "Concern",
    icon: "!",
    tone: "border-amber-300 bg-amber-50",
    badge: "bg-amber-100 text-amber-950",
  },
  unclear: {
    label: "Unclear",
    icon: "?",
    tone: "border-slate-200 bg-slate-50",
    badge: "bg-slate-200 text-slate-800",
  },
} as const;

function confidenceBand(confidence: number): string {
  if (confidence >= 0.8) return "Clear";
  if (confidence >= 0.5) return "Plausible";
  return "Unclear";
}

export function EvidenceObservationList({ observations }: { observations: EvidenceObservation[] }) {
  if (!observations.length) {
    return (
      <p className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        No observations were created because no uploaded evidence contained reviewable detail.
      </p>
    );
  }

  return (
    <ul className="space-y-3" aria-label="Evidence observations">
      {observations.map((observation) => {
        const presentation =
          presentations[observation.polarity as keyof typeof presentations] ?? {
            label: "Observation",
            icon: "?",
            tone: "border-slate-200 bg-slate-50",
            badge: "bg-slate-200 text-slate-800",
          };
        const percentage = Math.round(observation.confidence * 100);

        return (
          <li
            key={observation.id}
            className={`rounded-2xl border p-4 ${presentation.tone}`}
          >
            <div className="flex flex-wrap items-center gap-2">
              <span
                aria-label={`Polarity: ${presentation.label}`}
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold ${presentation.badge}`}
              >
                <span aria-hidden="true">{presentation.icon}</span>
                {presentation.label}
              </span>
              <span className="text-xs font-semibold text-slate-700">
                Confidence: {confidenceBand(observation.confidence)} ({percentage}%)
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-800">{observation.text}</p>
            <p className="mt-2 text-xs text-slate-600">
              Requirement reference: {observation.requirement_id}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <AIAnalysisStatus
                provider={observation.provider}
                fallback_used={observation.fallback_used}
              />
              {observation.validation_status === "validated" ? (
                <span className="text-xs font-medium text-slate-600">
                  Structured output validated
                </span>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
