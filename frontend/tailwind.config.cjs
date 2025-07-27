/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--color-bg)',
        surface: 'var(--color-surface)',
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        accent: 'var(--color-accent)',
        text: 'var(--color-text)',
        muted: 'var(--color-muted)',
        border: 'var(--color-border)',
      },
      fontFamily: {
        display: ['Orbitron', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
      },
      boxShadow: {
        soft: 'var(--shadow-soft)',
        medium: 'var(--shadow-medium)',
      },
      keyframes: {
        progress: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        glitch: {
          '0%, 100%': { clipPath: 'inset(0 0 0 0)' },
          '20%': { clipPath: 'inset(2% 0 70% 0)' },
          '40%': { clipPath: 'inset(50% 0 20% 0)' },
          '60%': { clipPath: 'inset(10% 0 50% 0)' },
          '80%': { clipPath: 'inset(80% 0 2% 0)' },
        },
        pulseGlow: {
          '0%,100%': { boxShadow: '0 0 8px #00e0ff80' },
          '50%': { boxShadow: '0 0 16px #00e0ff' },
        },
      },
      animation: {
        progress: 'progress 2s linear infinite',
        glitch: 'glitch 1s steps(2,end) infinite',
        glow: 'pulseGlow 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}; 