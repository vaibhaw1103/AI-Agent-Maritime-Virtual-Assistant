/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        'montserrat': ['var(--font-montserrat)', 'sans-serif'],
        'open-sans': ['var(--font-open-sans)', 'sans-serif'],
        'sans': ['var(--font-open-sans)', 'system-ui', 'sans-serif'],
      },
      colors: {
        background: "var(--color-background)",
        foreground: "var(--color-foreground)",
        card: {
          DEFAULT: "var(--color-card)",
          foreground: "var(--color-card-foreground)",
        },
        popover: {
          DEFAULT: "var(--color-popover)",
          foreground: "var(--color-popover-foreground)",
        },
        primary: {
          DEFAULT: "var(--color-primary)",
          foreground: "var(--color-primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--color-secondary)",
          foreground: "var(--color-secondary-foreground)",
        },
        muted: {
          DEFAULT: "var(--color-muted)",
          foreground: "var(--color-muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--color-accent)",
          foreground: "var(--color-accent-foreground)",
        },
        destructive: {
          DEFAULT: "var(--color-destructive)",
          foreground: "var(--color-destructive-foreground)",
        },
        border: "var(--color-border)",
        input: "var(--color-input)",
        ring: "var(--color-ring)",
        chart: {
          "1": "var(--color-chart-1)",
          "2": "var(--color-chart-2)",
          "3": "var(--color-chart-3)",
          "4": "var(--color-chart-4)",
          "5": "var(--color-chart-5)",
        },
        sidebar: {
          DEFAULT: "var(--color-sidebar)",
          foreground: "var(--color-sidebar-foreground)",
          primary: "var(--color-sidebar-primary)",
          "primary-foreground": "var(--color-sidebar-primary-foreground)",
          accent: "var(--color-sidebar-accent)",
          "accent-foreground": "var(--color-sidebar-accent-foreground)",
          border: "var(--color-sidebar-border)",
          ring: "var(--color-sidebar-ring)",
        },
      },
      borderRadius: {
        sm: "calc(var(--radius-sm, var(--radius) - 4px))",
        DEFAULT: "var(--radius-md, var(--radius))",
        md: "calc(var(--radius-md, var(--radius) - 2px))",
        lg: "var(--radius-lg, var(--radius))",
        xl: "calc(var(--radius-xl, var(--radius) + 4px))",
      },
    },
  },
  plugins: [
    require("tailwindcss-animate"),
  ],
}
