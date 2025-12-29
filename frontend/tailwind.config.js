/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'fintech': {
                    'bg': '#0B0F19',
                    'card': '#151B2B',
                    'hover': '#1E293B',
                    'primary': '#38BDF8',
                    'primary-dark': '#0284C7',
                    'text-primary': '#F1F5F9',
                    'text-secondary': '#94A3B8',
                    'text-muted': '#64748B',
                    'success': '#10B981',
                    'warning': '#F59E0B',
                    'error': '#EF4444',
                    'border': '#2D3748',
                },
                'brand-dark': '#0f172a', // Keeping for backward compat briefly
                'brand-primary': '#0ea5e9',
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
