import { AlertTriangle, Info, StickyNote } from "lucide-react";

type NoticeTone = "warning" | "info" | "neutral";

interface NoticeBannerProps {
  title?: string;
  children: React.ReactNode;
  tone?: NoticeTone;
  className?: string;
}

const TONE_STYLES: Record<NoticeTone, { wrap: string; icon: string }> = {
  warning: {
    wrap: "border-amber-200/80 bg-amber-50 text-amber-950",
    icon: "text-amber-600",
  },
  info: {
    wrap: "border-sky-200/80 bg-sky-50 text-sky-950",
    icon: "text-sky-600",
  },
  neutral: {
    wrap: "border-line bg-mist text-ink",
    icon: "text-slate",
  },
};

const TONE_ICON = {
  warning: AlertTriangle,
  info: Info,
  neutral: StickyNote,
} as const;

export function NoticeBanner({ title, children, tone = "warning", className = "" }: NoticeBannerProps) {
  const styles = TONE_STYLES[tone];
  const Icon = TONE_ICON[tone];

  return (
    <div
      className={`flex gap-3 rounded-2xl border px-4 py-3.5 text-sm leading-relaxed sm:px-5 ${styles.wrap} ${className}`}
    >
      <Icon className={`mt-0.5 h-[18px] w-[18px] shrink-0 ${styles.icon}`} aria-hidden="true" />
      <div className="min-w-0">
        {title ? <p className="mb-1 font-semibold">{title}</p> : null}
        <div className="text-sm leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
