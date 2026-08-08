import Link from "next/link";

import { SiteLogo } from "@/components/SiteLogo";

interface SiteFooterProps {
  maxWidth?: "4xl" | "5xl" | "6xl" | "7xl";
}

const WIDTH: Record<string, string> = {
  "4xl": "max-w-4xl",
  "5xl": "max-w-5xl",
  "6xl": "max-w-6xl",
  "7xl": "max-w-7xl",
};

export function SiteFooter({ maxWidth = "6xl" }: SiteFooterProps) {
  const widthClass = WIDTH[maxWidth] ?? WIDTH["6xl"];

  return (
    <footer className="mt-16 border-t border-slate-200/70 bg-white">
      <div className={`mx-auto flex flex-col gap-6 px-4 py-10 sm:px-6 md:flex-row md:items-start md:justify-between ${widthClass}`}>
        <div className="max-w-sm">
          <SiteLogo />
          <p className="mt-3 text-sm leading-relaxed text-slate-500">
            AI-assisted certification readiness for Sri Lankan food manufacturers. Preparation
            guidance only — not an official certification decision.
          </p>
        </div>
        <nav aria-label="Footer" className="flex flex-col gap-2 text-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Explore</span>
          <Link href="/product-quality/select" className="text-slate-600 transition-colors hover:text-leaf">
            Product Quality
          </Link>
          <Link href="/education" className="text-slate-600 transition-colors hover:text-leaf">
            Certification Guide
          </Link>
          <Link href="/my-assessments" className="text-slate-600 transition-colors hover:text-leaf">
            My Assessments
          </Link>
        </nav>
      </div>
      <div className={`mx-auto border-t border-slate-100 px-4 py-5 sm:px-6 ${widthClass}`}>
        <p className="text-xs text-slate-400">
          CertifyLK does not issue, guarantee, or replace SLS certification or an official
          inspection.
        </p>
      </div>
    </footer>
  );
}
