interface TierBadgeProps {
  tier: string;
  className?: string;
}

const TIER_STYLES: Record<string, { label: string; cls: string }> = {
  mandatory: { label: "Mandatory by law", cls: "bg-red-50 text-red-800 border-red-200" },
  market_required: { label: "Market required", cls: "bg-amber-50 text-amber-900 border-amber-200" },
  recommended: { label: "Recommended", cls: "bg-blue-50 text-blue-800 border-blue-200" },
  optional: { label: "Optional", cls: "bg-slate-100 text-slate-700 border-slate-200" },
};

export function TierBadge({ tier, className = "" }: TierBadgeProps) {
  const { label, cls } = TIER_STYLES[tier] ?? TIER_STYLES.optional;
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cls} ${className}`}
    >
      {label}
    </span>
  );
}
