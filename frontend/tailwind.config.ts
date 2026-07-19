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
        primary: "#2563EB",
        accent: "#0891B2",
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
        background: "#FAFBFC",
        surface: "#FFFFFF",
        border: "#E5E7EB",
        ink: "#111827",
        secondary: "#4B5563",
        muted: "#9CA3AF"
      },
      borderRadius: {
        button: "12px",
        input: "12px",
        card: "16px"
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"]
      },
      minHeight: {
        control: "44px"
      }
    }
  },
  plugins: []
};

export default config;
