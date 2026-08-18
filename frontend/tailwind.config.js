/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        bloom: {
          remember: '#0284c7',
          understand: '#2563eb',
          apply: '#059669',
          analyze: '#d97706',
          evaluate: '#ea580c',
          create: '#7c3aed',
        }
      }
    },
  },
  plugins: [],
};
