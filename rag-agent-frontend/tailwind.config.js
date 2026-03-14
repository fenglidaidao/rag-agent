/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Sora', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        bg: {
          base:    '#0d0f12',
          surface: '#13161b',
          elevated:'#1a1e25',
          border:  '#252932',
        },
        accent: {
          DEFAULT: '#00d4ff',
          dim:     '#00d4ff22',
          hover:   '#33ddff',
        },
        text: {
          primary:   '#e8eaf0',
          secondary: '#7a8394',
          muted:     '#454d5c',
        },
        success: '#00e5a0',
        warning: '#ffb347',
        danger:  '#ff4d6d',
      },
      animation: {
        'fade-in':    'fadeIn 0.2s ease-out',
        'slide-up':   'slideUp 0.25s ease-out',
        'pulse-dot':  'pulseDot 1.2s ease-in-out infinite',
        'stream-in':  'streamIn 0.1s ease-out',
      },
      keyframes: {
        fadeIn:    { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp:   { from: { opacity: 0, transform: 'translateY(8px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        pulseDot:  { '0%,100%': { opacity: 0.3, transform: 'scale(0.8)' }, '50%': { opacity: 1, transform: 'scale(1)' } },
        streamIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
      },
    },
  },
  plugins: [],
}
