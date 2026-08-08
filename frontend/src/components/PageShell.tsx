import type { ReactNode } from "react";

import { SiteHeader } from "@/components/SiteHeader";

interface PageShellProps {
  children: ReactNode;
  headerLinks?: { href: string; label: string }[];
  headerTrailing?: ReactNode;
  maxWidth?: "4xl" | "5xl" | "6xl";
  className?: string;
}

export function PageShell({
  children,
  headerLinks,
  headerTrailing,
  maxWidth = "6xl",
  className = "",
}: PageShellProps) {
  const widthClass =
    maxWidth === "4xl" ? "max-w-4xl" : maxWidth === "5xl" ? "max-w-5xl" : "max-w-6xl";

  return (
    <div className={`min-h-screen bg-surface ${className}`}>
      <SiteHeader links={headerLinks} trailing={headerTrailing} maxWidth={maxWidth} />
      <div className={`mx-auto px-4 py-8 sm:px-6 sm:py-10 ${widthClass}`}>{children}</div>
    </div>
  );
}
