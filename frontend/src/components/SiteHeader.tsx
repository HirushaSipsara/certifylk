"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";

import { SiteLogo } from "@/components/SiteLogo";

type NavLink = {
  href: string;
  label: string;
};

interface SiteHeaderProps {
  links?: NavLink[];
  trailing?: ReactNode;
  maxWidth?: "4xl" | "5xl" | "6xl";
}

const DEFAULT_LINKS: NavLink[] = [
  { href: "/my-assessments", label: "My Assessments" },
  { href: "/education", label: "Certification Guide" },
];

export function SiteHeader({
  links = DEFAULT_LINKS,
  trailing,
  maxWidth = "6xl",
}: SiteHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const widthClass =
    maxWidth === "4xl" ? "max-w-4xl" : maxWidth === "5xl" ? "max-w-5xl" : "max-w-6xl";

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 backdrop-blur-sm">
      <div className={`mx-auto flex items-center justify-between gap-4 px-4 py-3.5 sm:px-6 ${widthClass}`}>
        <SiteLogo />

        <div className="flex items-center gap-3">
          {trailing}

          <nav className="hidden items-center gap-1 md:flex">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-leaf"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <button
            type="button"
            className="inline-flex items-center justify-center rounded-lg border border-slate-200 p-2 text-slate-700 md:hidden"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              {menuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {menuOpen ? (
        <nav className="border-t border-slate-100 px-4 py-3 md:hidden">
          <div className="flex flex-col gap-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                onClick={() => setMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </nav>
      ) : null}
    </header>
  );
}
