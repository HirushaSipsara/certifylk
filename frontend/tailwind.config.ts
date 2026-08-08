import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // ── Foundation ────────────────────────────────────────────────
        ink: {
          DEFAULT: "#0c2723", // near-black forest green — headings & dark surfaces
          soft: "#123c34",
        },
        night: "#0a1f2b", // deep slate — hero / dark panels
        // Neutral surfaces
        sand: "#f5f8f6",
        surface: "#f5f8f6",
        mist: "#eef3f1",
        line: "#e2e9e6",
        slate: {
          DEFAULT: "#5b6b66", // muted body text on light
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
        // ── Brand: Track 1 (Product Quality) — emerald ───────────────
        leaf: "#0f8a70",
        "leaf-dark": "#0b6d58",
        lime: "#d9f99d",
        brand: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#0f8a70",
          700: "#0b6d58",
          800: "#095646",
          900: "#0c2723",
        },
        // ── Track 2 (Process & System) — indigo/navy ─────────────────
        navy: "#1e2b45",
        accent: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#1e2b45",
        },
        // ── Feedback ─────────────────────────────────────────────────
        coral: "#c2410c",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(12, 39, 35, 0.04), 0 8px 24px -12px rgba(12, 39, 35, 0.12)",
        "card-hover": "0 2px 4px rgba(12, 39, 35, 0.05), 0 16px 40px -16px rgba(12, 39, 35, 0.22)",
        soft: "0 1px 2px rgba(12, 39, 35, 0.05)",
      },
      keyframes: {
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(12px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both",
        "fade-in": "fade-in 0.4s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
