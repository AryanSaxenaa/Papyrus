import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PAPYRUS_E2E_BASE_URL ?? "https://papyrus-production-70fb.up.railway.app";

export default defineConfig({
  testDir: ".",
  timeout: 120_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
