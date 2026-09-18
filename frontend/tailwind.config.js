/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                commandDark: "#0B0F17",
                commandCard: "#161C28",
                commandAccent: "#00E5FF",
                commandAlert: "#FF3B30",
                commandWarning: "#FF9500",
            }
        },
    },
    plugins: [],
}