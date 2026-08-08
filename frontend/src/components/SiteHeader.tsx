"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { Menu, X } from "lucide-react";

import { SiteLogo } from "@/components/SiteLogo";

type NavLink = {
  href: string;
  label: string;
};

interface SiteHeaderProps {
  links?: NavLink[];
  trailing?: ReactNode;
  maxWidth?: "4xl" | "5xl" | "6xl" | "7xl";
}

const DEFAULT_LINKS: NavLink[] = [
  { href: "/my-assessments", label: "My Assessments" },
  { href: "/education", label: "Certification Guide" },
];

const WIDTH: Record<string, string> = {
  "4xl": "max-w-4xl",
  "5xl": "max-w-5xl",
  "6xl": "max-w-6xl",
  "7xl": "max-w-7xl",
};

export function SiteHeader({ links = DEFAULT_LINKS, trailing, maxWidth = "6xl" }: SiteHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();
  const widthClass = WIDTH[maxWidth] ?? WIDTH["6xl"];

  function isActive(href: string) {
    return pathname === href || pathname?.startsWith(`${href}/`);
  }

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-surface/80 backdrop-blur-md">
      <div className={`mx-auto flex items-center justify-between gap-4 px-4 py-3 sm:px-6 ${widthClass}`}>
        <SiteLogo />

        <div className="flex items-center gap-2 sm:gap-3">
          {trailing}

          <nav className="hidden items-center gap-1 md:flex">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={isActive(link.href) ? "page" : undefined}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive(link.href)
                    ? "bg-leaf/10 text-leaf-dark"
                    : "text-slate-600 hover:bg-slate-100/70 hover:text-ink"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 transition-colors hover:bg-slate-50 md:hidden"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {menuOpen ? (
        <nav className="border-t border-slate-100 bg-surface px-4 py-3 md:hidden">
          <div className="flex flex-col gap-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={isActive(link.href) ? "page" : undefined}
                className={`rounded-lg px-3 py-3 text-sm font-medium transition-colors ${
                  isActive(link.href) ? "bg-leaf/10 text-leaf-dark" : "text-slate-700 hover:bg-slate-100"
                }`}
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
