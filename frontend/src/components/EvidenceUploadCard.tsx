import type { ChangeEvent } from "react";

import type { EvidenceRequest } from "@/types";

interface Props {
  request: EvidenceRequest;
  busy: boolean;
  onUpload: (file: File) => Promise<void>;
  onUnavailable: () => Promise<void>;
}

export function EvidenceUploadCard({
  request,
  busy,
  onUpload,
  onUnavailable,
}: Props) {
  const resolved = request.status !== "requested";
  const accept = request.kind === "photo" ? "image/jpeg,image/png,image/webp" : "application/pdf";

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) await onUpload(file);
  }

  return (
    <article className="rounded-2xl border border-slate-200 p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-semibold text-ink">{request.title}</p>
          <p className="mt-1 text-sm text-slate-500">
            {request.kind === "photo" ? "JPEG, PNG or WebP · max 8 MB" : "PDF · max 12 MB"}
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold capitalize text-slate-600">
          {request.status.replace("_", " ")}
        </span>
      </div>
      {!resolved ? (
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <label className="cursor-pointer rounded-xl bg-leaf px-4 py-2 text-center font-semibold text-white hover:bg-ink">
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
            onClick={() => void onUnavailable()}
            disabled={busy}
            className="rounded-xl border border-slate-300 px-4 py-2 font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            I do not have this
          </button>
        </div>
      ) : null}
    </article>
  );
}
