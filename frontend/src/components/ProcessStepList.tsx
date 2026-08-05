import type { FieldErrors, UseFormRegister } from "react-hook-form";

export interface ProcessFormValues {
  steps: [string, string, string, string, string];
}

interface Props {
  register: UseFormRegister<ProcessFormValues>;
  errors?: FieldErrors<ProcessFormValues>;
}

export function ProcessStepList({ register, errors }: Props) {
  return (
    <div className="space-y-3">
      {[0, 1, 2, 3, 4].map((index) => (
        <div key={index} className="flex items-start gap-3">
          <span className="mt-2 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-emerald-100 font-bold text-leaf">
            {index + 1}
          </span>
          <div className="w-full">
            <label htmlFor={`step-${index}`} className="sr-only">
              Production step {index + 1}
            </label>
            <input
              id={`step-${index}`}
              {...register(`steps.${index}` as "steps.0" | "steps.1" | "steps.2" | "steps.3" | "steps.4")}
              placeholder={
                index === 0 ? "For example: Purchase and check ingredients" : `Step ${index + 1}`
              }
              className="w-full rounded-xl border border-slate-300 px-4 py-3 focus:border-leaf focus:outline-none focus:ring-2 focus:ring-emerald-100"
            />
            {errors?.steps?.[index]?.message ? (
              <p className="mt-1 text-sm text-coral">{errors.steps[index]?.message}</p>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
