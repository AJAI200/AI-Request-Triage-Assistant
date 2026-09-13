/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          bg: '#FFF8EE',
          surface: '#FFFFFF',
          tint: '#FFF4E5',
          border: '#FFE0B2',
        },
        orange: {
          brand: '#FF5C00',
          hover: '#E05200',
          light: '#FFEDD5',
          glow: 'rgba(255, 92, 0, 0.25)',
        },
        charcoal: {
          text: '#2D1F17',
          muted: '#7A6B63',
          border: '#E8DED8',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        'pill': '0 8px 24px rgba(255, 92, 0, 0.15)',
        'card': '0 12px 32px rgba(45, 31, 23, 0.08)',
        'lift': '0 20px 40px rgba(255, 92, 0, 0.2)',
      }
    },
  },
  plugins: [],
}
