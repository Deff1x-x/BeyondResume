import type { Config } from "tailwindcss";

/**
 * BeyondResume — Evidence Intelligence
 * Navy · Lime · Cyan (AI only) · Neutrals
 *
 * Colors resolve from CSS variables in styles/globals.css (single source of truth).
 * Do not hardcode palette hex here.
 */
const channel = (token: string) => `rgb(var(${token}) / <alpha-value>)`;

const navyScale = {
  DEFAULT: channel("--color-primary"),
  50: channel("--color-background"),
  100: channel("--color-surface-subtle"),
  200: channel("--color-border"),
  300: channel("--color-border-strong"),
  400: channel("--color-ink-muted"),
  500: channel("--color-ink-muted"),
  600: channel("--color-ink-secondary"),
  700: channel("--color-ink"),
  800: channel("--color-primary"),
  900: channel("--color-primary-hover"),
  foreground: channel("--color-primary-foreground"),
  hover: channel("--color-primary-hover")
} as const;

/** Bright fill; use `accent-muted` / `accent-foreground` for text. Never white on lime. */
const limeScale = {
  DEFAULT: channel("--color-accent"),
  50: channel("--color-accent-soft"),
  100: channel("--color-accent-soft"),
  200: channel("--color-accent"),
  300: channel("--color-accent"),
  400: channel("--color-accent"),
  500: channel("--color-accent-hover"),
  600: channel("--color-accent-muted"),
  700: channel("--color-accent-muted"),
  800: channel("--color-accent-muted"),
  900: channel("--color-accent-foreground"),
  foreground: channel("--color-accent-foreground"),
  muted: channel("--color-accent-muted"),
  hover: channel("--color-accent-hover"),
  soft: channel("--color-accent-soft")
} as const;

/** AI signal only. Never white on cyan. */
const cyanScale = {
  DEFAULT: channel("--color-ai"),
  50: channel("--color-ai-soft"),
  100: channel("--color-ai-soft"),
  200: channel("--color-ai"),
  300: channel("--color-ai"),
  400: channel("--color-ai"),
  500: channel("--color-ai"),
  600: channel("--color-ai-hover"),
  700: channel("--color-ai-muted"),
  800: channel("--color-ai-muted"),
  900: channel("--color-ai-foreground"),
  foreground: channel("--color-ai-foreground"),
  muted: channel("--color-ai-muted"),
  hover: channel("--color-ai-hover"),
  soft: channel("--color-ai-soft")
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
        /^(bg|text|border|ring|from|to|via|shadow)-(primary|accent|ai|verified|success|warning|danger)(-\d+|-(foreground|muted|hover|soft|emphasis))?$/
    },
    {
      pattern:
        /^(bg|text|border|ring)-(primary|accent|ai|verified|success|warning|danger)\/(5|10|15|20|25|30|40|45|50|75|90)$/
    }
  ],
  theme: {
    extend: {
      colors: {
        primary: navyScale,
        accent: limeScale,
        verified: {
          DEFAULT: channel("--color-verified"),
          foreground: channel("--color-accent-foreground"),
          muted: channel("--color-verified-muted"),
          hover: channel("--color-accent-hover"),
          soft: channel("--color-verified-soft")
        },
        ai: cyanScale,
        success: {
          DEFAULT: channel("--color-success"),
          soft: channel("--color-success-soft"),
          muted: channel("--color-success-muted"),
          foreground: channel("--color-success-foreground"),
          50: channel("--color-success-soft"),
          100: channel("--color-success-soft"),
          500: channel("--color-success"),
          700: channel("--color-success-muted")
        },
        warning: {
          DEFAULT: channel("--color-warning"),
          soft: channel("--color-warning-soft"),
          muted: channel("--color-warning-muted"),
          foreground: channel("--color-warning-foreground"),
          emphasis: channel("--color-warning-emphasis"),
          50: channel("--color-warning-soft"),
          100: channel("--color-warning-soft"),
          500: channel("--color-warning-emphasis"),
          700: channel("--color-warning")
        },
        danger: {
          DEFAULT: channel("--color-danger"),
          soft: channel("--color-danger-soft"),
          muted: channel("--color-danger-muted"),
          foreground: channel("--color-danger-foreground"),
          50: channel("--color-danger-soft"),
          100: channel("--color-danger-soft"),
          500: channel("--color-danger"),
          700: channel("--color-danger")
        },
        background: channel("--color-background"),
        "surface-subtle": channel("--color-surface-subtle"),
        "surface-elevated": channel("--color-surface-elevated"),
        surface: {
          DEFAULT: channel("--color-surface"),
          subtle: channel("--color-surface-subtle"),
          elevated: channel("--color-surface-elevated"),
          accent: channel("--color-surface-accent")
        },
        border: {
          DEFAULT: channel("--color-border"),
          strong: channel("--color-border-strong")
        },
        ink: {
          DEFAULT: channel("--color-ink"),
          secondary: channel("--color-ink-secondary"),
          muted: channel("--color-ink-muted")
        },
        secondary: channel("--color-ink-secondary"),
        muted: channel("--color-ink-muted"),
        "focus-ring": channel("--color-focus-ring"),
        selection: "var(--color-selection)",
        overlay: "var(--color-overlay)"
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
        card: "var(--shadow-card)",
        "card-hover": "var(--shadow-card-hover)",
        float: "var(--shadow-float)",
        accent: "var(--shadow-accent)",
        ai: "var(--shadow-ai)"
      }
    }
  },
  plugins: []
};

export default config;
