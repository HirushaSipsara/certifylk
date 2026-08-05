"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AssessmentShell } from "@/components/AssessmentShell";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { useAssessment } from "@/hooks/useAssessment";
import { ApiError, api } from "@/lib/api";

const schema = z
  .object({
    product_name: z.string().min(2, "Enter your product name."),
    food_category: z.enum(["processed_food", "bakery", "beverage", "spice_product", "other"]),
    other_category_text: z.string().optional(),
    production_location: z.enum(["home_kitchen", "shared_kitchen", "small_workshop", "small_factory", "other"]),
    production_location_other: z.string().optional(),
    production_scale: z.enum(["micro", "small", "growing"]),
    worker_range: z.enum(["1_5", "6_10", "11_25", "26_plus"]),
    packaging_type: z.enum(["glass_bottle", "plastic_bottle", "pouch", "box", "jar", "other"]),
    packaging_type_other: z.string().optional(),
    storage_method: z.enum(["room_temperature", "refrigerated", "frozen", "mixed", "other"]),
    storage_method_other: z.string().optional(),
    shelf_life_range: z.enum(["under_one_week", "one_to_four_weeks", "one_to_six_months", "over_six_months"]),
    existing_certification: z.string().min(1, "Enter none or a certification name."),
    production_record_frequency: z.enum(["every_batch", "sometimes", "never"]),
    additional_information: z.string().max(2000).default(""),
  })
  .superRefine((value, context) => {
    const checks: Array<[string, string | undefined, keyof typeof value]> = [
      [value.food_category, value.other_category_text, "other_category_text"],
      [value.production_location, value.production_location_other, "production_location_other"],
      [value.packaging_type, value.packaging_type_other, "packaging_type_other"],
      [value.storage_method, value.storage_method_other, "storage_method_other"],
    ];
    checks.forEach(([selected, detail, path]) => {
      if (selected === "other" && !detail?.trim()) {
        context.addIssue({ code: z.ZodIssueCode.custom, message: "Please describe this option.", path: [path] });
      }
    });
  });

type ProfileValues = z.infer<typeof schema>;

const defaults: ProfileValues = {
  product_name: "",
  food_category: "processed_food",
  production_location: "home_kitchen",
  production_scale: "micro",
  worker_range: "1_5",
  packaging_type: "glass_bottle",
  storage_method: "room_temperature",
  shelf_life_range: "one_to_six_months",
  existing_certification: "none",
  production_record_frequency: "sometimes",
  additional_information: "",
};

const selectClass = "mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-3 focus:border-leaf focus:outline-none focus:ring-2 focus:ring-emerald-100";
const inputClass = "mt-1 w-full rounded-xl border border-slate-300 px-3 py-3 focus:border-leaf focus:outline-none focus:ring-2 focus:ring-emerald-100";

function FieldError({ message }: { message?: string }) {
  return message ? <p className="mt-1 text-sm text-coral">{message}</p> : null;
}

export default function ProfilePage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const router = useRouter();
  const { assessment, loading, error: loadError, refresh } = useAssessment(assessmentId);
  const [busy, setBusy] = useState(false);
  const [error, setErrorMessage] = useState<string | null>(null);
  const { register, handleSubmit, watch, reset, setError, formState: { errors } } = useForm<ProfileValues>({ resolver: zodResolver(schema), defaultValues: defaults });

  useEffect(() => {
    if (assessment?.profile && Object.keys(assessment.profile).length) {
      reset({ ...defaults, ...(assessment.profile as Partial<ProfileValues>) });
    }
  }, [assessment, reset]);

  async function submit(values: ProfileValues) {
    if (busy) return;
    setBusy(true);
    setErrorMessage(null);
    try {
      await api.saveProfile(assessmentId, values);
      await api.adaptivePlan(assessmentId);
      router.push(`/assessment/${assessmentId}/process`);
    } catch (caught) {
      if (caught instanceof ApiError) {
        caught.details.forEach((detail) => {
          const field = detail.field?.split(".").at(-1) as keyof ProfileValues | undefined;
          if (field && field in defaults) setError(field, { message: detail.message });
        });
      }
      setErrorMessage(caught instanceof Error ? caught.message : "Could not save your profile.");
      setBusy(false);
    }
  }

  if (loading) return <LoadingOverlay message="Loading your saved profile…" />;

  return (
    <AssessmentShell currentStep={1} title="Tell us about your food product" description="Use simple answers—no certification knowledge is needed. Your answers are saved before the next step.">
      {busy ? <LoadingOverlay message="Saving your profile and choosing relevant process questions…" /> : null}
      {loadError ? <ErrorAlert message={loadError} onRetry={() => void refresh()} /> : null}
      {error ? <div className="mb-5"><ErrorAlert message={error} /></div> : null}
      <form onSubmit={handleSubmit(submit)} className="space-y-5" noValidate>
        <div>
          <label htmlFor="product_name" className="font-semibold">Product name</label>
          <input id="product_name" {...register("product_name")} className={inputClass} />
          <FieldError message={errors.product_name?.message} />
        </div>
        <div>
          <label htmlFor="food_category" className="font-semibold">Food category</label>
          <select id="food_category" {...register("food_category")} className={selectClass}>
            <option value="processed_food">Processed food</option><option value="bakery">Bakery product</option><option value="beverage">Beverage</option><option value="spice_product">Spice product</option><option value="other">Other</option>
          </select>
          {watch("food_category") === "other" ? <><input aria-label="Other food category" {...register("other_category_text")} className={inputClass} placeholder="Describe the category" /><FieldError message={errors.other_category_text?.message} /></> : null}
        </div>
        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label htmlFor="production_location" className="font-semibold">Production location</label>
            <select id="production_location" {...register("production_location")} className={selectClass}>
              <option value="home_kitchen">Home kitchen</option><option value="shared_kitchen">Shared kitchen</option><option value="small_workshop">Small workshop</option><option value="small_factory">Small factory</option><option value="other">Other</option>
            </select>
            {watch("production_location") === "other" ? <><input aria-label="Other production location" {...register("production_location_other")} className={inputClass} /><FieldError message={errors.production_location_other?.message} /></> : null}
          </div>
          <div>
            <label htmlFor="production_scale" className="font-semibold">Production scale</label>
            <select id="production_scale" {...register("production_scale")} className={selectClass}><option value="micro">Micro / occasional batches</option><option value="small">Small / regular batches</option><option value="growing">Growing production</option></select>
          </div>
          <div>
            <label htmlFor="worker_range" className="font-semibold">Number of workers</label>
            <select id="worker_range" {...register("worker_range")} className={selectClass}><option value="1_5">1–5</option><option value="6_10">6–10</option><option value="11_25">11–25</option><option value="26_plus">26 or more</option></select>
          </div>
          <div>
            <label htmlFor="packaging_type" className="font-semibold">Packaging type</label>
            <select id="packaging_type" {...register("packaging_type")} className={selectClass}><option value="glass_bottle">Glass bottle</option><option value="plastic_bottle">Plastic bottle</option><option value="pouch">Pouch</option><option value="box">Box</option><option value="jar">Jar</option><option value="other">Other</option></select>
            {watch("packaging_type") === "other" ? <><input aria-label="Other packaging type" {...register("packaging_type_other")} className={inputClass} /><FieldError message={errors.packaging_type_other?.message} /></> : null}
          </div>
          <div>
            <label htmlFor="storage_method" className="font-semibold">Storage method</label>
            <select id="storage_method" {...register("storage_method")} className={selectClass}><option value="room_temperature">Room temperature</option><option value="refrigerated">Refrigerated</option><option value="frozen">Frozen</option><option value="mixed">Mixed</option><option value="other">Other</option></select>
            {watch("storage_method") === "other" ? <><input aria-label="Other storage method" {...register("storage_method_other")} className={inputClass} /><FieldError message={errors.storage_method_other?.message} /></> : null}
          </div>
          <div>
            <label htmlFor="shelf_life_range" className="font-semibold">Shelf-life range</label>
            <select id="shelf_life_range" {...register("shelf_life_range")} className={selectClass}><option value="under_one_week">Under one week</option><option value="one_to_four_weeks">1–4 weeks</option><option value="one_to_six_months">1–6 months</option><option value="over_six_months">Over 6 months</option></select>
          </div>
        </div>
        <div>
          <label htmlFor="existing_certification" className="font-semibold">Existing certification</label>
          <input id="existing_certification" {...register("existing_certification")} className={inputClass} placeholder="Enter none or a known minor certification" />
          <FieldError message={errors.existing_certification?.message} />
        </div>
        <div>
          <label htmlFor="production_record_frequency" className="font-semibold">How often do you record production?</label>
          <select id="production_record_frequency" {...register("production_record_frequency")} className={selectClass}><option value="every_batch">Every batch</option><option value="sometimes">Sometimes</option><option value="never">Never</option></select>
        </div>
        <div>
          <label htmlFor="additional_information" className="font-semibold">Additional information <span className="font-normal text-slate-500">(optional)</span></label>
          <textarea id="additional_information" {...register("additional_information")} rows={4} className={inputClass} />
        </div>
        <button type="submit" disabled={busy || Boolean(loadError)} className="w-full rounded-xl bg-leaf px-6 py-3 font-bold text-white hover:bg-ink disabled:opacity-50">Continue to manufacturing process</button>
      </form>
    </AssessmentShell>
  );
}
