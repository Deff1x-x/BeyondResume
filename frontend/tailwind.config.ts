import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#4F46E5",
        accent: "#06B6D4",
        success: "#059669",
        warning: "#D97706",
        danger: "#E11D48",
        background: "#F6F7FB",
        surface: {
          DEFAULT: "#FFFFFF",
          subtle: "#F0F2F8",
          elevated: "#FFFFFF",
          accent: "#EEF2FF",
          glass: "rgba(255, 255, 255, 0.76)"
        },
        border: {
          DEFAULT: "#E4E7EF",
          strong: "#C9CFDD"
        },
        ink: "#172033",
        secondary: "#667085",
        muted: "#98A2B3",
        "focus-ring": "#6366F1"
      },
      borderRadius: {
        button: "10px",
        input: "10px",
        card: "18px",
        dialog: "22px"
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"]
      },
      minHeight: {
        control: "44px"
      },
      boxShadow: {
        card: "0 1px 2px rgba(16, 24, 40, 0.03), 0 8px 24px rgba(16, 24, 40, 0.06)",
        "card-hover": "0 2px 4px rgba(16, 24, 40, 0.04), 0 16px 34px rgba(47, 46, 129, 0.12)",
        float: "0 20px 50px rgba(55, 48, 163, 0.18)"
      }
    }
  },
  plugins: []
};

export default config;
