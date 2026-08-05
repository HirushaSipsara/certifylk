import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17352e",
        leaf: "#19715e",
        lime: "#d9f99d",
        sand: "#fffaf0",
        coral: "#c54f3d"
      },
      boxShadow: {
        card: "0 14px 40px rgba(23, 53, 46, 0.09)"
      }
    }
  },
  plugins: []
};

export default config;
