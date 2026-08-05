import type { Question } from "@/types";

import { OtherTextField } from "./OtherTextField";

interface Props {
  question: Question;
  value?: string;
  onChange: (value: string) => void;
  otherText?: string;
  onOtherChange?: (value: string) => void;
  error?: string;
}

export function QuestionCard({
  question,
  value,
  onChange,
  otherText,
  onOtherChange,
  error,
}: Props) {
  const options = question.allows_other
    ? [...question.options, { value: "other", label: "Other" }]
    : question.options;
  return (
    <fieldset className="rounded-2xl border border-slate-200 p-4">
      <legend className="px-1 font-semibold text-ink">{question.text}</legend>
      <div className="mt-3 space-y-2">
        {options.map((option) => (
          <label
            key={option.value}
            className="flex cursor-pointer items-start gap-3 rounded-xl p-2 hover:bg-emerald-50"
          >
            <input
              type="radio"
              name={question.id}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              className="mt-1 accent-leaf"
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
      {value === "other" && onOtherChange ? (
        <OtherTextField
          id={`${question.id}-other`}
          value={otherText}
          onChange={onOtherChange}
          error={!otherText?.trim() ? "Please describe your answer." : undefined}
        />
      ) : null}
      {error ? <p className="mt-2 text-sm text-coral">{error}</p> : null}
    </fieldset>
  );
}
