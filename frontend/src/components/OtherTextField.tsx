interface Props {
  id: string;
  label?: string;
  value?: string;
  onChange: (value: string) => void;
  error?: string;
}

export function OtherTextField({
  id,
  label = "Please describe",
  value = "",
  onChange,
  error,
}: Props) {
  return (
    <div className="mt-3">
      <label htmlFor={id} className="block text-sm font-semibold text-ink">
        {label}
      </label>
      <input
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 focus:border-leaf focus:outline-none focus:ring-2 focus:ring-emerald-100"
        aria-invalid={Boolean(error)}
      />
      {error ? <p className="mt-1 text-sm text-coral">{error}</p> : null}
    </div>
  );
}
