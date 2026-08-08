import { Scale, Store, Star, Lightbulb, type LucideIcon } from "lucide-react";

interface TierBadgeProps {
  tier: string;
  className?: string;
  withIcon?: boolean;
}

const TIER_STYLES: Record<string, { label: string; cls: string; icon: LucideIcon }> = {
  mandatory: {
    label: "Mandatory by law",
    cls: "bg-red-50 text-red-800 border-red-200",
    icon: Scale,
  },
  market_required: {
    label: "Market required",
    cls: "bg-amber-50 text-amber-900 border-amber-200",
    icon: Store,
  },
  recommended: {
    label: "Recommended",
    cls: "bg-sky-50 text-sky-800 border-sky-200",
    icon: Star,
  },
  optional: {
    label: "Optional",
    cls: "bg-slate-100 text-slate-700 border-slate-200",
    icon: Lightbulb,
  },
};

export function TierBadge({ tier, className = "", withIcon = true }: TierBadgeProps) {
  const { label, cls, icon: Icon } = TIER_STYLES[tier] ?? TIER_STYLES.optional;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cls} ${className}`}
    >
      {withIcon ? <Icon className="h-3.5 w-3.5" /> : null}
      {label}
    </span>
  );
}
