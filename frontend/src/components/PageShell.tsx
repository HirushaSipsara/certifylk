import type { ReactNode } from "react";

import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

interface PageShellProps {
  children: ReactNode;
  headerLinks?: { href: string; label: string }[];
  headerTrailing?: ReactNode;
  maxWidth?: "4xl" | "5xl" | "6xl" | "7xl";
  className?: string;
  footer?: boolean;
}

const WIDTH: Record<string, string> = {
  "4xl": "max-w-4xl",
  "5xl": "max-w-5xl",
  "6xl": "max-w-6xl",
  "7xl": "max-w-7xl",
};

export function PageShell({
  children,
  headerLinks,
  headerTrailing,
  maxWidth = "6xl",
  className = "",
  footer = true,
}: PageShellProps) {
  const widthClass = WIDTH[maxWidth] ?? WIDTH["6xl"];

  return (
    <div className={`flex min-h-screen flex-col bg-surface ${className}`}>
      <SiteHeader links={headerLinks} trailing={headerTrailing} maxWidth={maxWidth} />
      <main className={`mx-auto w-full flex-1 px-4 py-8 sm:px-6 sm:py-10 ${widthClass}`}>{children}</main>
      {footer ? <SiteFooter maxWidth={maxWidth} /> : null}
    </div>
  );
}
