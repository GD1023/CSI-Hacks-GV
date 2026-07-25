// Shared Tailwind Play CDN config, loaded on every page after the CDN script tag.
// Design tokens (colors/fonts/shadows) and reusable component classes live here
// once, instead of one-off utility soup scattered across pages.
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#eff6ff',
                    100: '#dbeafe',
                    200: '#bfdbfe',
                    300: '#93c5fd',
                    400: '#60a5fa',
                    500: '#3b82f6',
                    600: '#2563eb',
                    700: '#1d4ed8',
                    800: '#1e40af',
                    900: '#1e3a8a',
                },
                neutral: {
                    50: '#f8fafc',
                    100: '#f1f5f9',
                    200: '#e2e8f0',
                    300: '#cbd5e1',
                    400: '#94a3b8',
                    500: '#64748b',
                    600: '#475569',
                    700: '#334155',
                    800: '#1e293b',
                    900: '#0f172a',
                },
                accent: {
                    50: '#fffbeb',
                    100: '#fef3c7',
                    400: '#fbbf24',
                    500: '#f59e0b',
                    600: '#d97706',
                },
            },
            fontFamily: {
                sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
            },
            boxShadow: {
                soft: '0 2px 8px -2px rgba(15, 23, 42, 0.08), 0 4px 16px -4px rgba(15, 23, 42, 0.06)',
                'soft-lg': '0 8px 24px -4px rgba(15, 23, 42, 0.12), 0 16px 40px -8px rgba(15, 23, 42, 0.10)',
            },
        },
    },
    plugins: [
        function ({ addComponents }) {
            addComponents({
                '.container-page': {
                    maxWidth: '72rem',
                    marginLeft: 'auto',
                    marginRight: 'auto',
                    paddingLeft: '1rem',
                    paddingRight: '1rem',
                    '@media (min-width: 640px)': { paddingLeft: '1.5rem', paddingRight: '1.5rem' },
                    '@media (min-width: 1024px)': { paddingLeft: '2rem', paddingRight: '2rem' },
                },
                '.btn': {
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    borderRadius: '0.75rem',
                    fontWeight: '600',
                    fontSize: '0.9375rem',
                    padding: '0.55rem 1.1rem',
                    transition: 'background-color 0.15s ease, color 0.15s ease, transform 0.1s ease, box-shadow 0.15s ease',
                    textDecoration: 'none',
                    cursor: 'pointer',
                    border: '1px solid transparent',
                },
                '.btn:active': { transform: 'scale(0.97)' },
                '.btn-primary': {
                    backgroundColor: '#2563eb',
                    color: '#ffffff',
                    boxShadow: '0 2px 8px -2px rgba(15, 23, 42, 0.08), 0 4px 16px -4px rgba(15, 23, 42, 0.06)',
                },
                '.btn-primary:hover': { backgroundColor: '#1d4ed8' },
                '.btn-ghost': {
                    backgroundColor: 'transparent',
                    color: '#334155',
                },
                '.btn-ghost:hover': { backgroundColor: '#f1f5f9', color: '#1e293b' },
                '.btn-outline': {
                    backgroundColor: 'transparent',
                    color: '#2563eb',
                    borderColor: '#bfdbfe',
                },
                '.btn-outline:hover': { backgroundColor: '#eff6ff' },
                '.nav-link': {
                    display: 'inline-block',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '0.5rem',
                    fontSize: '0.9375rem',
                    fontWeight: '500',
                    color: '#334155',
                    textDecoration: 'none',
                    transition: 'background-color 0.15s ease, color 0.15s ease',
                },
                '.nav-link:hover': { backgroundColor: '#f1f5f9', color: '#1e293b' },
                '.nav-current': {
                    color: '#1d4ed8',
                    fontWeight: '600',
                    backgroundColor: '#eff6ff',
                },
                '.nav-restricted': {
                    display: 'none',
                },
            });
        },
    ],
};
