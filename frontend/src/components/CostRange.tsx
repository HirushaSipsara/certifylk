function money(value: number) {
  return new Intl.NumberFormat("en-LK", { maximumFractionDigits: 0 }).format(value);
}

export function CostRange({
  label,
  range,
  quoteRequired,
}: {
  label: string;
  range: { min: number; max: number; currency: string };
  quoteRequired?: boolean;
}) {
  if (quoteRequired) {
    return (
      <p className="text-sm text-slate-600">
        <span className="font-semibold text-ink">{label}:</span>{" "}
        <span className="text-amber-800 font-medium">Quote required</span>
      </p>
    );
  }

  const isZero = range.min === 0 && range.max === 0;
  return (
    <p className="text-sm text-slate-600">
      <span className="font-semibold text-ink">{label}:</span>{" "}
      {isZero ? "Included / No extra fee" : `${range.currency} ${money(range.min)}–${money(range.max)}`}
    </p>
  );
}
