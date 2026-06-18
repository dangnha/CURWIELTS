/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        band9: '#22c55e',
        band8: '#3b82f6',
        band7: '#8b5cf6',
        band6: '#f59e0b',
        band5: '#ef4444',
      },
    },
  },
  plugins: [],
}
