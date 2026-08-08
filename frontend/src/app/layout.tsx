import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Inter, Plus_Jakarta_Sans } from "next/font/google";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "CertifyLK · AI-assisted certification readiness",
    template: "%s · CertifyLK",
  },
  description:
    "CertifyLK helps Sri Lankan food manufacturers find the right certification pathway, understand requirements, and see readiness gaps with an explainable, cost-aware roadmap.",
  keywords: [
    "certification readiness",
    "SLS Mark",
    "GMP",
    "HACCP",
    "ISO 22000",
    "Sri Lanka food manufacturing",
  ],
  applicationName: "CertifyLK",
  authors: [{ name: "CertifyLK" }],
};

export const viewport: Viewport = {
  themeColor: "#0c2723",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={`bg-surface ${inter.variable} ${jakarta.variable}`}>
      <body className="min-h-screen bg-surface font-sans text-ink antialiased">{children}</body>
    </html>
  );
}
