import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          base: "#070912",
          deep: "#040611",
          panel: "#0f1322",
          card: "rgba(20, 24, 42, 0.55)"
        },
        brand: {
          50: "#eef2ff",
          100: "#dbe5ff",
          200: "#b6c7ff",
          300: "#8aa6ff",
          400: "#5d80ff",
          500: "#3a5dff",
          600: "#2a44e6",
          700: "#1f33b4",
          800: "#1a2a8e",
          900: "#152271"
        },
        accent: {
          cyan: "#22d3ee",
          violet: "#a855f7",
          emerald: "#34d399",
          rose: "#f43f5e",
          amber: "#fbbf24"
        }
      },
      backgroundImage: {
        "grid-dark":
          "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.06) 1px, transparent 0)",
        "hero-glow":
          "radial-gradient(60% 60% at 50% 0%, rgba(58, 93, 255, 0.25) 0%, transparent 60%), radial-gradient(40% 40% at 90% 100%, rgba(168, 85, 247, 0.18) 0%, transparent 70%)"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(255,255,255,0.04), 0 20px 60px -20px rgba(58, 93, 255, 0.35)",
        card: "0 1px 0 rgba(255,255,255,0.05) inset, 0 30px 60px -30px rgba(0,0,0,0.6)"
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-1000px 0" },
          "100%": { backgroundPosition: "1000px 0" }
        },
        floaty: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" }
        },
        pulseRing: {
          "0%": { boxShadow: "0 0 0 0 rgba(58, 93, 255, 0.45)" },
          "70%": { boxShadow: "0 0 0 10px rgba(58, 93, 255, 0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(58, 93, 255, 0)" }
        },
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      },
      animation: {
        shimmer: "shimmer 1.8s linear infinite",
        floaty: "floaty 4s ease-in-out infinite",
        pulseRing: "pulseRing 2s ease-out infinite",
        fadeIn: "fadeIn 0.35s ease-out both"
      }
    }
  },
  plugins: []
};

export default config;
