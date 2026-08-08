import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17352e",
        leaf: "#19715e",
        lime: "#d9f99d",
        sand: "#f8faf9",
        surface: "#f8faf9",
        coral: "#c54f3d",
      },
      boxShadow: {
        card: "0 8px 30px rgba(23, 53, 46, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
