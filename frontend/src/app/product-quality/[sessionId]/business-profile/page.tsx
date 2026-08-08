"use client";

import { useState } from "react";
import { useRouter, useSearchParams, useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";

import { ErrorAlert } from "@/components/ErrorAlert";
import { FlowHeader, FlowSteps } from "@/components/FlowHeader";
import { Spinner } from "@/components/LoadingState";
import { api, ApiError } from "@/lib/api";

const STEPS = ["Choose product", "Business profile", "Certificates"];

const BUSINESS_TYPES = [
  { value: "sole_proprietor", label: "Sole proprietor" },
  { value: "partnership", label: "Partnership" },
  { value: "limited_company", label: "Limited company" },
  { value: "co_operative", label: "Co-operative" },
  { value: "other", label: "Other" },
];

const SCALES = [
  { value: "micro", label: "Micro (home / cottage)" },
  { value: "small", label: "Small (≤ 25 workers)" },
  { value: "medium", label: "Medium (26–100 workers)" },
  { value: "large", label: "Large (100+ workers)" },
];

const MARKETS = [
  { value: "local_direct", label: "Local — direct to consumer" },
  { value: "local_retail", label: "Local — small retail / grocery" },
  { value: "supermarket", label: "Supermarket chains" },
  { value: "institutional", label: "Government / institutional" },
  { value: "export", label: "Export markets" },
];

const VOLUME_RANGES = [
  { value: "under_100", label: "< 100 kg / month" },
  { value: "100_500", label: "100–500 kg / month" },
  { value: "500_2000", label: "500–2000 kg / month" },
  { value: "over_2000", label: "> 2000 kg / month" },
];

export default function BusinessProfilePage() {
  const router = useRouter();
  const params = useParams<{ sessionId: string }>();
  const searchParams = useSearchParams();
  const productSlug = searchParams.get("product") ?? "";
  const sessionId = params.sessionId; // This is the assessment ID

  const [form, setForm] = useState({
    name: "",
    business_type: "sole_proprietor",
    years_operating: "",
    scale: "micro",
    market: [] as string[],
    existing_certifications: [] as string[],
    has_food_licence: "no",
    monthly_volume_range: "",
    additional_info: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function setField(key: string, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
    setFieldErrors((e) => ({ ...e, [key]: "" }));
  }

  function toggleMarket(v: string) {
    setForm((f) => ({
      ...f,
      market: f.market.includes(v) ? f.market.filter((m) => m !== v) : [...f.market, v],
    }));
  }

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!form.name.trim() || form.name.trim().length < 2)
      errors.name = "Business name is required (min 2 characters).";
    if (form.market.length === 0) errors.market = "Select at least one target market.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    setError(null);

    try {
      await api.createBusinessProfile({
        name: form.name.trim(),
        business_type: form.business_type,
        years_operating: form.years_operating ? parseInt(form.years_operating) : null,
        scale: form.scale,
        market: form.market,
        existing_certifications: form.existing_certifications,
        has_food_licence: form.has_food_licence,
        monthly_volume_range: form.monthly_volume_range || null,
        additional_info: form.additional_info,
        assessment_id: sessionId,
        product_slug: productSlug || null,
      });
      router.push(`/product-quality/${sessionId}/certificates`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        const fe: Record<string, string> = {};
        for (const d of err.details) {
          if (d.field) fe[d.field] = d.message;
        }
        setFieldErrors(fe);
      } else {
        setError("Something went wrong. Please try again.");
      }
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface">
      <FlowHeader maxWidth="3xl" trailing={<FlowSteps steps={STEPS} current={2} tone="leaf" />} />

      <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
        <div className="mb-8">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-leaf/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-leaf-dark">
            Track 1 · Product Quality
          </span>
          <h1 className="section-title mt-3">Tell us about your business</h1>
          <p className="section-lead">
            This information helps the AI determine which certifications apply to your situation. All
            fields are used only for this readiness assessment.
          </p>
        </div>

        {error ? <ErrorAlert message={error} className="mb-6" /> : null}

        <form onSubmit={(e) => void onSubmit(e)} className="space-y-6" noValidate>
          {/* Business name */}
          <div className="card !p-6">
            <label htmlFor="bp-name" className="field-label">
              Business / trading name *
            </label>
            <input
              id="bp-name"
              type="text"
              value={form.name}
              onChange={(e) => setField("name", e.target.value)}
              placeholder="e.g. Dilmah Foods (Pvt) Ltd"
              aria-invalid={Boolean(fieldErrors.name)}
              className={`field-input ${fieldErrors.name ? "border-coral/50 bg-coral/5" : ""}`}
            />
            {fieldErrors.name ? (
              <p className="mt-1.5 text-xs font-medium text-coral">{fieldErrors.name}</p>
            ) : null}
          </div>

          {/* Business type */}
          <div className="card !p-6">
            <label htmlFor="bp-type" className="field-label">
              Business type
            </label>
            <select
              id="bp-type"
              value={form.business_type}
              onChange={(e) => setField("business_type", e.target.value)}
              className="field-input"
            >
              {BUSINESS_TYPES.map((bt) => (
                <option key={bt.value} value={bt.value}>
                  {bt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Scale */}
          <div className="card !p-6">
            <p className="field-label">Production scale</p>
            <div className="grid grid-cols-2 gap-3">
              {SCALES.map((s) => {
                const active = form.scale === s.value;
                return (
                  <button
                    key={s.value}
                    type="button"
                    id={`bp-scale-${s.value}`}
                    onClick={() => setField("scale", s.value)}
                    aria-pressed={active}
                    className={`rounded-xl border p-3 text-left text-sm transition-all ${
                      active
                        ? "border-leaf bg-leaf/5 font-semibold text-leaf-dark"
                        : "border-slate-200 bg-white text-slate hover:border-leaf/40"
                    }`}
                  >
                    {s.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Target markets */}
          <div className="card !p-6">
            <p className="field-label">
              Target markets *{" "}
              <span className="font-normal text-slate-400">(select all that apply)</span>
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {MARKETS.map((m) => {
                const active = form.market.includes(m.value);
                return (
                  <label
                    key={m.value}
                    id={`bp-market-${m.value}`}
                    className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition-all ${
                      active
                        ? "border-leaf bg-leaf/5"
                        : "border-slate-200 bg-white hover:border-leaf/40"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={() => toggleMarket(m.value)}
                      className="h-4 w-4 accent-leaf"
                    />
                    <span className="text-sm text-ink">{m.label}</span>
                  </label>
                );
              })}
            </div>
            {fieldErrors.market ? (
              <p className="mt-1.5 text-xs font-medium text-coral">{fieldErrors.market}</p>
            ) : null}
          </div>

          {/* Monthly volume */}
          <div className="card !p-6">
            <label htmlFor="bp-volume" className="field-label">
              Approximate monthly production volume
            </label>
            <select
              id="bp-volume"
              value={form.monthly_volume_range}
              onChange={(e) => setField("monthly_volume_range", e.target.value)}
              className="field-input"
            >
              <option value="">Not sure / prefer not to say</option>
              {VOLUME_RANGES.map((v) => (
                <option key={v.value} value={v.value}>
                  {v.label}
                </option>
              ))}
            </select>
          </div>

          {/* Food licence */}
          <div className="card !p-6">
            <p className="field-label">
              Do you currently hold a Food Business Registration / Food Licence from the CAA or MOH?
            </p>
            <div className="flex flex-col gap-3 sm:flex-row">
              {[
                { value: "yes", label: "Yes" },
                { value: "no", label: "No" },
                { value: "in_progress", label: "In progress" },
              ].map((opt) => {
                const active = form.has_food_licence === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    id={`bp-licence-${opt.value}`}
                    onClick={() => setField("has_food_licence", opt.value)}
                    aria-pressed={active}
                    className={`flex-1 rounded-xl border py-3 text-sm font-medium transition-all ${
                      active
                        ? "border-leaf bg-leaf/5 text-leaf-dark"
                        : "border-slate-200 bg-white text-slate hover:border-leaf/40"
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Years operating */}
          <div className="card !p-6">
            <label htmlFor="bp-years" className="field-label">
              Years in operation (optional)
            </label>
            <input
              id="bp-years"
              type="number"
              min={0}
              max={200}
              value={form.years_operating}
              onChange={(e) => setField("years_operating", e.target.value)}
              placeholder="e.g. 3"
              className="field-input"
            />
          </div>

          {/* Additional info */}
          <div className="card !p-6">
            <label htmlFor="bp-info" className="field-label">
              Anything else we should know? (optional)
            </label>
            <textarea
              id="bp-info"
              rows={3}
              value={form.additional_info}
              onChange={(e) => setField("additional_info", e.target.value)}
              placeholder="e.g. We currently supply to 3 supermarkets, and we want to start exporting to the Maldives."
              className="field-input resize-none"
            />
          </div>

          {/* Submit */}
          <div className="flex items-center justify-between pt-2">
            <Link
              href="/product-quality/select"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-slate transition-colors hover:text-ink"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Back
            </Link>
            <button id="bp-submit" type="submit" disabled={submitting} className="btn-primary px-8">
              {submitting ? (
                <>
                  <Spinner className="text-white" />
                  Saving…
                </>
              ) : (
                <>
                  Continue
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </>
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
