import type { ChangeEvent } from "react";
import { CheckCircle2, XCircle, RotateCcw, Upload } from "lucide-react";

import type { EvidenceRequest } from "@/types";

interface Props {
  request: EvidenceRequest;
  busy: boolean;
  onUpload: (file: File) => Promise<void>;
  onUnavailable: () => Promise<void>;
  /** Called when the user wants to remove/reset a resolved item to re-upload or re-mark */
  onRemove?: () => Promise<void>;
}

const STATUS_BADGES: Record<string, { label: string; className: string; Icon: React.ElementType }> = {
  uploaded: {
    label: "Uploaded",
    className: "bg-emerald-100 text-emerald-700",
    Icon: CheckCircle2,
  },
  unavailable: {
    label: "Marked unavailable",
    className: "bg-amber-100 text-amber-700",
    Icon: XCircle,
  },
  requested: {
    label: "Awaiting upload",
    className: "bg-slate-100 text-slate-600",
    Icon: Upload,
  },
};

export function EvidenceUploadCard({
  request,
  busy,
  onUpload,
  onUnavailable,
  onRemove,
}: Props) {
  const resolved = request.status !== "requested";
  const accept = request.kind === "photo" ? "image/jpeg,image/png,image/webp" : "application/pdf";
  const badge = STATUS_BADGES[request.status] ?? STATUS_BADGES.requested;
  const { Icon } = badge;

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    // Reset the input value so the same file can be re-selected after removal
    event.target.value = "";
    if (file) await onUpload(file);
  }

  return (
    <article
      className={`rounded-2xl border p-4 transition-colors ${
        resolved ? "border-slate-200 bg-slate-50" : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-ink">{request.title}</p>
          <p className="mt-1 text-sm text-slate-500">
            {request.kind === "photo" ? "JPEG, PNG or WebP · max 8 MB" : "PDF · max 12 MB"}
          </p>
        </div>
        <span
          className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold whitespace-nowrap ${badge.className}`}
        >
          <Icon className="h-3.5 w-3.5" aria-hidden="true" />
          {badge.label}
        </span>
      </div>

      {resolved ? (
        /* Show remove/re-upload action for resolved items */
        onRemove ? (
          <div className="mt-3 flex items-center gap-2">
            <button
              type="button"
              id={`remove-evidence-${request.id}`}
              onClick={() => void onRemove()}
              disabled={busy}
              className="flex items-center gap-1.5 rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100 hover:text-red-600 hover:border-red-200 transition-colors disabled:opacity-50"
            >
              <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
              {busy ? "Removing…" : "Remove & re-upload"}
            </button>
          </div>
        ) : null
      ) : (
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <label
            id={`upload-label-${request.id}`}
            className="cursor-pointer rounded-xl bg-leaf px-4 py-2 text-center font-semibold text-white hover:bg-ink transition-colors"
          >
            {busy ? "Working…" : `Choose ${request.kind}`}
            <input
              aria-label={`Upload ${request.title}`}
              type="file"
              accept={accept}
              disabled={busy}
              className="sr-only"
              onChange={(event) => void handleFile(event)}
            />
          </label>
          <button
            type="button"
            id={`unavailable-${request.id}`}
            onClick={() => void onUnavailable()}
            disabled={busy}
            className="rounded-xl border border-slate-300 px-4 py-2 font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-colors"
          >
            I do not have this
          </button>
        </div>
      )}
    </article>
  );
}
