/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'dark-bg': '#0f172a',    // Slate 900
                'dark-card': '#1e293b',  // Slate 800
                'primary': '#3b82f6',    // Blue 500
                'accent': '#8b5cf6',     // Violet 500
            }
        },
    },
    plugins: [],
}
