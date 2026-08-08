type NoticeTone = "warning" | "info" | "neutral";

interface NoticeBannerProps {
  title?: string;
  children: React.ReactNode;
  tone?: NoticeTone;
  className?: string;
}

const TONE_STYLES: Record<NoticeTone, string> = {
  warning: "border-amber-200 bg-amber-50 text-amber-950",
  info: "border-blue-200 bg-blue-50 text-blue-950",
  neutral: "border-slate-200 bg-slate-50 text-slate-800",
};

export function NoticeBanner({ title, children, tone = "warning", className = "" }: NoticeBannerProps) {
  return (
    <div
      className={`rounded-xl border px-4 py-3.5 text-sm leading-relaxed sm:px-5 ${TONE_STYLES[tone]} ${className}`}
    >
      {title ? <p className="mb-1 font-semibold">{title}</p> : null}
      <div className="text-sm leading-relaxed">{children}</div>
    </div>
  );
}
