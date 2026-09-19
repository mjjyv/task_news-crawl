import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        crt: {
          bg: "#0A0A0A",
          surface: "#121212",
          panel: "#171717",
          border: "#262626",
          phosphor: "#EAEAEA",
          muted: "#8A8A8A",
          hazard: "#E61919",
          pulse: "#4AF626",
        },
        brand: {
          50: "#fdf2f2",
          100: "#fde8e8",
          200: "#fbd5d5",
          500: "#e61919", // Aviation / Hazard Red
          600: "#cc1414",
          700: "#b30e0e",
          800: "#800a0a",
        },
      },
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "JetBrains Mono",
          "IBM Plex Mono",
          "Consolas",
          "Courier Prime",
          "monospace",
        ],
        serif: ["Georgia", "Cambria", "Times New Roman", "serif"],
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
export default config;
