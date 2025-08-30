/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                border: "hsl(214, 32%, 91%)",
                input: "hsl(214, 32%, 91%)",
                ring: "hsl(215, 20%, 65%)",
                background: "hsl(0, 0%, 100%)",
                foreground: "hsl(224, 71%, 4%)",
                primary: {
                    DEFAULT: "hsl(262, 83%, 58%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                secondary: {
                    DEFAULT: "hsl(210, 40%, 96%)",
                    foreground: "hsl(222, 84%, 5%)",
                },
                destructive: {
                    DEFAULT: "hsl(0, 84%, 60%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                muted: {
                    DEFAULT: "hsl(210, 40%, 96%)",
                    foreground: "hsl(215, 16%, 47%)",
                },
                accent: {
                    DEFAULT: "hsl(210, 40%, 96%)",
                    foreground: "hsl(222, 84%, 5%)",
                },
                popover: {
                    DEFAULT: "hsl(0, 0%, 100%)",
                    foreground: "hsl(224, 71%, 4%)",
                },
                card: {
                    DEFAULT: "hsl(0, 0%, 100%)",
                    foreground: "hsl(224, 71%, 4%)",
                },
            },
            borderRadius: {
                lg: "0.5rem",
                md: "calc(0.5rem - 2px)",
                sm: "calc(0.5rem - 4px)",
            },
            animation: {
                'fade-in': 'fadeIn 0.2s ease-out',
                'slide-up': 'slideUp 0.2s ease-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                }
            }
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
    ],
}
