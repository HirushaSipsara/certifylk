import type { ComponentType, ReactNode } from "react";

interface IconProps {
  className?: string;
  "aria-hidden"?: boolean;
}

interface PageHeaderProps {
  eyebrow?: ReactNode;
  eyebrowIcon?: ComponentType<IconProps>;
  eyebrowTone?: "leaf" | "navy" | "amber";
  title: string;
  /** Supporting copy under the title. `lead` and `description` are aliases. */
  lead?: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

const EYEBROW_TONES: Record<string, string> = {
  leaf: "bg-leaf/10 text-leaf-dark",
  navy: "bg-accent-100 text-accent-800",
  amber: "bg-amber-100 text-amber-800",
};

export function PageHeader({
  eyebrow,
  eyebrowIcon: EyebrowIcon,
  eyebrowTone = "leaf",
  title,
  lead,
  description,
  actions,
  className = "",
}: PageHeaderProps) {
  const supporting = lead ?? description;

  return (
    <div className={`flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between ${className}`}>
      <div className="min-w-0">
        {eyebrow ? (
          <span
            className={`mb-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${EYEBROW_TONES[eyebrowTone]}`}
          >
            {EyebrowIcon ? <EyebrowIcon className="h-3.5 w-3.5" aria-hidden={true} /> : null}
            {eyebrow}
          </span>
        ) : null}
        <h1 className="section-title">{title}</h1>
        {supporting ? <p className="section-lead">{supporting}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}

interface EyebrowProps {
  children: ReactNode;
  tone?: "leaf" | "navy" | "amber";
}

export function Eyebrow({ children, tone = "leaf" }: EyebrowProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${EYEBROW_TONES[tone]}`}
    >
      {children}
    </span>
  );
}
