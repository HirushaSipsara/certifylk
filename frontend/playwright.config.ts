import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./src/test/e2e",
  use: { baseURL: "http://localhost:3000" },
  webServer: {
    command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
    url: "http://localhost:3000",
    reuseExistingServer: true
  }
});
