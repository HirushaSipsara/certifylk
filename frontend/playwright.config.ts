import { defineConfig } from "@playwright/test";

const port = process.env.PLAYWRIGHT_FRONTEND_PORT ?? "3000";
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${port}`;

export default defineConfig({
  testDir: "./src/test/e2e",
  use: { baseURL },
  webServer: {
    command: `npm run dev -- --hostname 127.0.0.1 --port ${port}`,
    url: baseURL,
    reuseExistingServer: true
  }
});
