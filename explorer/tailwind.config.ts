import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#009b87',
          light: '#00c9a7',
          dark: '#007a6c',
        },
        surface: {
          DEFAULT: '#18181b',
          hover: '#27272a',
        },
        border: {
          DEFAULT: '#27272a',
          subtle: '#1e1e21',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config;
