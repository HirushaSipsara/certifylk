function money(value: number) {
  return new Intl.NumberFormat("en-LK", { maximumFractionDigits: 0 }).format(value);
}

export function CostRange({ label, range }: { label: string; range: { min: number; max: number; currency: string } }) {
  return (
    <p className="text-sm text-slate-600">
      <span className="font-semibold text-ink">{label}:</span> {range.currency} {money(range.min)}–{money(range.max)}
    </p>
  );
}
