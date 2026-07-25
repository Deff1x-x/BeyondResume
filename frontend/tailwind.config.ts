import type { Config } from "tailwindcss";

/**
 * BeyondResume — Evidence Intelligence
 * Midnight Ink · Electric Lime · Signal Cyan · Cloud
 * Semantic tokens only — no purple / indigo brand.
 */
const midnightInk = {
  DEFAULT: "#111827",
  50: "#F3F4F6",
  100: "#E5E7EB",
  200: "#D1D5DB",
  300: "#9CA3AF",
  400: "#6B7280",
  500: "#4B5563",
  600: "#374151",
  700: "#1F2937",
  800: "#111827",
  900: "#0B1220"
} as const;

/** Bright fill; use `accent-muted` / `accent-foreground` for text. */
const electricLime = {
  DEFAULT: "#A3E635",
  50: "#F7FEE7",
  100: "#ECFCCB",
  200: "#D9F99D",
  300: "#BEF264",
  400: "#A3E635",
  500: "#84CC16",
  600: "#65A30D",
  700: "#4D7C0F",
  800: "#3F6212",
  900: "#365314",
  foreground: "#111827",
  muted: "#3F6212",
  hover: "#84CC16"
} as const;

/** Bright signal; use `ai-muted` for readable text on light surfaces. */
const signalCyan = {
  DEFAULT: "#22D3EE",
  50: "#ECFEFF",
  100: "#CFFAFE",
  200: "#A5F3FC",
  300: "#67E8F9",
  400: "#22D3EE",
  500: "#06B6D4",
  600: "#0891B2",
  700: "#0E7490",
  800: "#155E75",
  900: "#164E63",
  foreground: "#111827",
  muted: "#0E7490",
  hover: "#06B6D4"
} as const;

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  safelist: [
    {
      pattern:
        /^(bg|text|border|ring|from|to|via|shadow)-(primary|accent|ai|verified|success|warning|danger)(-\d+|-(foreground|muted|hover))?$/
    },
    {
      pattern:
        /^(bg|text|border|ring)-(primary|accent|ai|verified|success|warning|danger)\/(5|10|15|20|25|30|40|45|50|75|90)$/
    }
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          ...midnightInk,
          foreground: "#FFFFFF",
          hover: "#0B1220"
        },
        accent: electricLime,
        verified: {
          DEFAULT: "#A3E635",
          foreground: "#111827",
          muted: "#3F6212",
          hover: "#84CC16"
        },
        ai: signalCyan,
        success: {
          DEFAULT: "#16A36A",
          50: "#ECFDF5",
          100: "#D1FAE5",
          500: "#16A36A",
          700: "#0F766E",
          muted: "#0F766E",
          foreground: "#FFFFFF"
        },
        warning: {
          DEFAULT: "#F59E0B",
          50: "#FFFBEB",
          100: "#FEF3C7",
          500: "#F59E0B",
          700: "#B45309",
          muted: "#B45309",
          foreground: "#111827"
        },
        danger: {
          DEFAULT: "#DC4C5B",
          50: "#FEF2F2",
          100: "#FEE2E2",
          500: "#DC4C5B",
          700: "#B91C1C",
          muted: "#B91C1C",
          foreground: "#FFFFFF"
        },
        background: "#F4F7F8",
        "surface-subtle": "#EAF0F2",
        "surface-elevated": "#FFFFFF",
        surface: {
          DEFAULT: "#FFFFFF",
          subtle: "#EAF0F2",
          elevated: "#FFFFFF",
          accent: "#F0F7F4"
        },
        border: {
          DEFAULT: "#DDE5E8",
          strong: "#C5D0D4"
        },
        ink: {
          DEFAULT: "#111827",
          secondary: "#475569",
          muted: "#64748B"
        },
        secondary: "#64748B",
        muted: "#64748B",
        "focus-ring": "#22D3EE",
        selection: "rgba(163, 230, 53, 0.22)",
        overlay: "rgba(17, 24, 39, 0.48)"
      },
      borderRadius: {
        control: "10px",
        button: "10px",
        input: "10px",
        badge: "9999px",
        card: "16px",
        panel: "12px",
        dialog: "20px"
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "system-ui", "sans-serif"]
      },
      fontSize: {
        display: ["3.5rem", { lineHeight: "1.05", letterSpacing: "-0.04em", fontWeight: "600" }],
        "page-title": ["2rem", { lineHeight: "1.15", letterSpacing: "-0.03em", fontWeight: "600" }],
        "section-title": ["1.25rem", { lineHeight: "1.3", letterSpacing: "-0.02em", fontWeight: "600" }],
        "card-title": ["0.9375rem", { lineHeight: "1.35", letterSpacing: "-0.01em", fontWeight: "600" }],
        body: ["0.875rem", { lineHeight: "1.55", fontWeight: "400" }],
        caption: ["0.75rem", { lineHeight: "1.4", fontWeight: "400" }],
        label: ["0.8125rem", { lineHeight: "1.3", fontWeight: "500" }],
        metric: ["1.5rem", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "600" }]
      },
      minHeight: {
        control: "44px"
      },
      transitionDuration: {
        fast: "150ms",
        normal: "250ms",
        slow: "600ms"
      },
      transitionTimingFunction: {
        standard: "cubic-bezier(0.2, 0, 0, 1)",
        emphasized: "cubic-bezier(0.22, 1, 0.36, 1)"
      },
      boxShadow: {
        card: "0 1px 2px rgba(17, 24, 39, 0.04), 0 8px 24px rgba(17, 24, 39, 0.05)",
        "card-hover":
          "0 2px 4px rgba(17, 24, 39, 0.05), 0 14px 32px rgba(17, 24, 39, 0.08)",
        float: "0 18px 44px rgba(17, 24, 39, 0.12)",
        accent: "0 8px 24px rgba(163, 230, 53, 0.28)",
        ai: "0 8px 24px rgba(34, 211, 238, 0.22)"
      }
    }
  },
  plugins: []
};

export default config;
