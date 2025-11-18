/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        primary: '#00548F',
        'primary-light': '#0073B7',
        'primary-dark': '#003d66',
        secondary: '#4D0A2E',
        background: '#F5F7FA',
        'text-primary': '#1a1a1a',
        'text-secondary': '#666666',
        'text-tertiary': '#999999',
        'bg-alt': '#FAFBFC',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      transitionDuration: {
        0: '0ms',
        300: '300ms',
        500: '500ms',
      },
    },
  },
  plugins: [],
};
