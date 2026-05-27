/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            colors: {
                'dark-bg':      '#080f1a',
                'dark-card':    '#111827',
                'dark-surface': '#0d1524',
                'primary':      '#3b82f6',
                'accent':       '#8b5cf6',
            },
            boxShadow: {
                'card':      '0 1px 3px 0 rgba(0,0,0,0.4), 0 1px 2px -1px rgba(0,0,0,0.4)',
                'card-md':   '0 4px 12px 0 rgba(0,0,0,0.5)',
                'glow-blue': '0 0 20px -4px rgba(59,130,246,0.35)',
            },
        },
    },
    plugins: [],
}
