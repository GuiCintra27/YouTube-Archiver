import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Lato', 'sans-serif'],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Custom brand colors
        teal: {
          DEFAULT: "#1bd1c8",
          light: "#33f6e0",
          dark: "#15a8a1",
        },
        cyan: {
          DEFAULT: "#33f6e0",
          light: "#5ff9e8",
          dark: "#1bd1c8",
        },
        yellow: {
          DEFAULT: "#f7d46b",
          light: "#f9e08f",
          dark: "#f0a73a",
        },
        orange: {
          DEFAULT: "#f0a73a",
          light: "#f7d46b",
          dark: "#e08620",
        },
        purple: {
          DEFAULT: "#8b6cf6",
          light: "#a78bfa",
          dark: "#7c3aed",
        },
        navy: {
          DEFAULT: "#0b1221",
          light: "#121d33",
          dark: "#050b16",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        'glow-teal': '0 0 20px rgba(27, 209, 200, 0.3), 0 0 40px rgba(27, 209, 200, 0.1)',
        'glow-yellow': '0 0 20px rgba(247, 212, 107, 0.3), 0 0 40px rgba(247, 212, 107, 0.1)',
        'glow-purple': '0 0 20px rgba(139, 108, 246, 0.3), 0 0 40px rgba(139, 108, 246, 0.1)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-teal': 'linear-gradient(135deg, #1bd1c8 0%, #33f6e0 100%)',
        'gradient-yellow': 'linear-gradient(135deg, #f7d46b 0%, #f0a73a 100%)',
        'gradient-purple': 'linear-gradient(135deg, #8b6cf6 0%, #a78bfa 100%)',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'gradient': 'gradient-shift 3s ease infinite',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
