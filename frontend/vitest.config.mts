import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const sourceRoot = fileURLToPath(new URL("./src", import.meta.url));

export default defineConfig({
  oxc: { jsx: { runtime: "automatic" } },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
    exclude: ["src/test/e2e/**", "node_modules/**"]
  },
  resolve: {
    alias: { "@": sourceRoot }
  }
});
