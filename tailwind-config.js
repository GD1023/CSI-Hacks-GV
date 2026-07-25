// Shared Tailwind Play CDN config, loaded on every page after the CDN script tag.
// Design tokens (colors/fonts/shadows) and reusable component classes live here
// once, instead of one-off utility soup scattered across pages.
//
// Theme: "Reading Room" — content-first and typographic. Near-white ground,
// hairline rules instead of cards or shadows, one restrained pine-green accent
// used only for links and interactive elements. Archivo carries headings/UI
// chrome; Source Serif 4 carries body copy (see style.css).
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#eff6f3',
                    100: '#d9ece3',
                    200: '#b3d9c8',
                    300: '#84bfa8',
                    400: '#4f9c82',
                    500: '#1f6f57',
                    600: '#1a5f4a',
                    700: '#164e3d',
                    800: '#123f32',
                    900: '#0f342a',
                },
                neutral: {
                    50: '#faf9f7',
                    100: '#f3f1ed',
                    200: '#e5e3de',
                    300: '#d2cfc7',
                    400: '#a8a49b',
                    500: '#807c73',
                    600: '#6b6f76',
                    700: '#4a473f',
                    800: '#2c2a25',
                    900: '#16171b',
                },
            },
            fontFamily: {
                sans: ['Archivo', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
                serif: ['"Source Serif 4"', 'ui-serif', 'Georgia', 'serif'],
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
                    gap: '0.4rem',
                    fontFamily: 'Archivo, ui-sans-serif, system-ui, sans-serif',
                    fontWeight: '700',
                    fontSize: '0.875rem',
                    padding: '0.4rem 0.25rem',
                    borderRadius: '2px',
                    transition: 'color 0.15s ease, border-color 0.15s ease, background-color 0.15s ease',
                    textDecoration: 'none',
                    cursor: 'pointer',
                    border: 'none',
                    borderBottom: '1px solid transparent',
                },
                '.btn:active': { opacity: '0.75' },
                '.btn-primary': {
                    color: '#1f6f57',
                    borderBottomColor: '#1f6f57',
                },
                '.btn-primary:hover': { color: '#164e3d', borderBottomColor: '#164e3d' },
                '.btn-ghost': {
                    color: '#6b6f76',
                },
                '.btn-ghost:hover': { color: '#16171b' },
                '.btn-outline': {
                    color: '#1f6f57',
                    borderBottomColor: '#1f6f57',
                },
                '.btn-outline:hover': { color: '#164e3d', borderBottomColor: '#164e3d' },
                '.nav-link': {
                    display: 'inline-block',
                    padding: '0.5rem 0.6rem',
                    fontFamily: 'Archivo, ui-sans-serif, system-ui, sans-serif',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#6b6f76',
                    textDecoration: 'none',
                    transition: 'color 0.15s ease',
                },
                '.nav-link:hover': { color: '#16171b' },
                '.nav-current': {
                    color: '#1f6f57',
                    fontWeight: '700',
                },
                '.nav-restricted': {
                    display: 'none',
                },
            });
        },
    ],
};
