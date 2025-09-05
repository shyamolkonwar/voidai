/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx,js,jsx}",
    "./components/**/*.{ts,tsx,js,jsx}"
  ],
  theme: {
    extend: {
      colors: {
        'grok-blue': '#2f6bf3',
        'grok-purple': '#8b5cf6'
      },
      boxShadow: {
        'figma-soft': '0 10px 30px rgba(2,6,23,0.6), inset 0 1px 0 rgba(255,255,255,0.02)'
      },
      backgroundImage: {
        'radial-glow': 'radial-gradient(ellipse at center, rgba(63,94,251,0.14) 0%, rgba(136,77,255,0.06) 40%, transparent 60%)',
      }
    }
  },
  plugins: []
}
