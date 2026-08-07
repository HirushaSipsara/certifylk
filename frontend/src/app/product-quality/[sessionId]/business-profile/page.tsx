"use client";

import { useState } from "react";
import { useRouter, useSearchParams, useParams } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

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
    if (!form.name.trim() || form.name.trim().length < 2) errors.name = "Business name is required (min 2 characters).";
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
    <div className="min-h-screen bg-gradient-to-br from-[#fffaf0] via-[#f0faf5] to-[#e8f5f0]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">🍃</span>
            <span className="font-bold text-emerald-800 text-lg">CertifyLK</span>
          </Link>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="w-6 h-6 rounded-full bg-gray-200 text-gray-400 flex items-center justify-center text-xs font-bold">1</span>
            <span>→</span>
            <span className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold">2</span>
            <span className="text-emerald-700 font-medium hidden sm:inline">Business profile</span>
            <span className="hidden sm:inline">→</span>
            <span className="w-6 h-6 rounded-full bg-gray-200 text-gray-400 items-center justify-center text-xs font-bold hidden sm:flex">3</span>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-emerald-900">
            Tell us about your business
          </h1>
          <p className="text-gray-500 mt-2 text-sm leading-relaxed">
            This information helps the AI determine which certifications apply to your situation.
            All fields are used only for this readiness assessment.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl p-4 mb-6">
            {error}
          </div>
        )}

        <form onSubmit={(e) => void onSubmit(e)} className="space-y-6" noValidate>
          {/* Business name */}
          <div>
            <label htmlFor="bp-name" className="block text-sm font-semibold text-gray-700 mb-1">
              Business / trading name *
            </label>
            <input
              id="bp-name"
              type="text"
              value={form.name}
              onChange={(e) => setField("name", e.target.value)}
              placeholder="e.g. Dilmah Foods (Pvt) Ltd"
              className={`w-full border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 ${
                fieldErrors.name ? "border-red-300 bg-red-50" : "border-gray-200 bg-white"
              }`}
            />
            {fieldErrors.name && <p className="text-xs text-red-600 mt-1">{fieldErrors.name}</p>}
          </div>

          {/* Business type */}
          <div>
            <label htmlFor="bp-type" className="block text-sm font-semibold text-gray-700 mb-1">
              Business type
            </label>
            <select
              id="bp-type"
              value={form.business_type}
              onChange={(e) => setField("business_type", e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
            >
              {BUSINESS_TYPES.map((bt) => (
                <option key={bt.value} value={bt.value}>{bt.label}</option>
              ))}
            </select>
          </div>

          {/* Scale */}
          <div>
            <p className="text-sm font-semibold text-gray-700 mb-2">Production scale</p>
            <div className="grid grid-cols-2 gap-3">
              {SCALES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  id={`bp-scale-${s.value}`}
                  onClick={() => setField("scale", s.value)}
                  className={`text-left p-3 rounded-xl border-2 text-sm transition-all ${
                    form.scale === s.value
                      ? "border-emerald-500 bg-emerald-50 font-medium text-emerald-800"
                      : "border-gray-200 bg-white text-gray-600 hover:border-emerald-200"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Target markets */}
          <div>
            <p className="text-sm font-semibold text-gray-700 mb-2">
              Target markets * <span className="font-normal text-gray-400">(select all that apply)</span>
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {MARKETS.map((m) => (
                <label
                  key={m.value}
                  id={`bp-market-${m.value}`}
                  className={`flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                    form.market.includes(m.value)
                      ? "border-emerald-500 bg-emerald-50"
                      : "border-gray-200 bg-white hover:border-emerald-200"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={form.market.includes(m.value)}
                    onChange={() => toggleMarket(m.value)}
                    className="accent-emerald-500"
                  />
                  <span className="text-sm text-gray-700">{m.label}</span>
                </label>
              ))}
            </div>
            {fieldErrors.market && (
              <p className="text-xs text-red-600 mt-1">{fieldErrors.market}</p>
            )}
          </div>

          {/* Monthly volume */}
          <div>
            <label htmlFor="bp-volume" className="block text-sm font-semibold text-gray-700 mb-1">
              Approximate monthly production volume
            </label>
            <select
              id="bp-volume"
              value={form.monthly_volume_range}
              onChange={(e) => setField("monthly_volume_range", e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
            >
              <option value="">Not sure / prefer not to say</option>
              {VOLUME_RANGES.map((v) => (
                <option key={v.value} value={v.value}>{v.label}</option>
              ))}
            </select>
          </div>

          {/* Food licence */}
          <div>
            <p className="text-sm font-semibold text-gray-700 mb-2">
              Do you currently hold a Food Business Registration / Food Licence from the CAA or MOH?
            </p>
            <div className="flex gap-3">
              {[
                { value: "yes", label: "Yes" },
                { value: "no", label: "No" },
                { value: "in_progress", label: "In progress" },
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  id={`bp-licence-${opt.value}`}
                  onClick={() => setField("has_food_licence", opt.value)}
                  className={`flex-1 py-3 rounded-xl border-2 text-sm font-medium transition-all ${
                    form.has_food_licence === opt.value
                      ? "border-emerald-500 bg-emerald-50 text-emerald-800"
                      : "border-gray-200 bg-white text-gray-600 hover:border-emerald-200"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Years operating */}
          <div>
            <label htmlFor="bp-years" className="block text-sm font-semibold text-gray-700 mb-1">
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
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>

          {/* Additional info */}
          <div>
            <label htmlFor="bp-info" className="block text-sm font-semibold text-gray-700 mb-1">
              Anything else we should know? (optional)
            </label>
            <textarea
              id="bp-info"
              rows={3}
              value={form.additional_info}
              onChange={(e) => setField("additional_info", e.target.value)}
              placeholder="e.g. We currently supply to 3 supermarkets, and we want to start exporting to the Maldives."
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-400 resize-none"
            />
          </div>

          {/* Submit */}
          <div className="flex justify-between items-center pt-2">
            <Link
              href="/product-quality/select"
              className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
            >
              ← Back
            </Link>
            <button
              id="bp-submit"
              type="submit"
              disabled={submitting}
              className="bg-emerald-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Saving…
                </>
              ) : (
                "Continue →"
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
