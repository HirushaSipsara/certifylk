import Link from "next/link";
import { ShieldCheck } from "lucide-react";

interface SiteLogoProps {
  href?: string;
  className?: string;
  tone?: "default" | "onDark";
}

export function SiteLogo({ href = "/", className = "", tone = "default" }: SiteLogoProps) {
  const wordmark = tone === "onDark" ? "text-white" : "text-ink";

  const content = (
    <>
      <span
        aria-hidden="true"
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-leaf text-white shadow-soft transition-transform group-hover:scale-105"
      >
        <ShieldCheck className="h-5 w-5" strokeWidth={2.2} />
      </span>
      <span className={`font-display text-lg font-bold tracking-tight ${wordmark}`}>
        Certify<span className="text-leaf">LK</span>
      </span>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={`group inline-flex items-center gap-2.5 ${className}`}>
        {content}
      </Link>
    );
  }

  return <span className={`inline-flex items-center gap-2.5 ${className}`}>{content}</span>;
}
