/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17221c",
        moss: "#245c3a",
        mint: "#dff4e6",
        sand: "#f7f3ea",
        coral: "#ef765c"
      },
      boxShadow: { panel: "0 18px 50px rgba(23, 34, 28, 0.14)" },
    },
  },
  plugins: [],
};
