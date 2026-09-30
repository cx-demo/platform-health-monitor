// SYS-4419 — browser behaviour tests for the /dashboard fleet plate.
// The page is served by the real FastAPI app through uvicorn; specs replace
// GET /platforms with synthetic records where a scenario needs them.
const { defineConfig, devices } = require("@playwright/test");

const PORT = Number(process.env.PHM_BROWSER_TEST_PORT || 8765);
const PYTHON = process.env.PHM_PYTHON || "python";

module.exports = defineConfig({
  testDir: "tests/browser",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: [
    ["list"],
    ["junit", { outputFile: "reports/browser.xml" }],
    ["html", { outputFolder: "reports/playwright-report", open: "never" }],
  ],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    acceptDownloads: true,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `${PYTHON} -m uvicorn src.main:app --host 127.0.0.1 --port ${PORT}`,
    url: `http://127.0.0.1:${PORT}/dashboard`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
