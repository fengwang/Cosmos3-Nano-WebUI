import { Module } from "node:module";
import path from "node:path";

import { defineConfig, devices } from "@playwright/test";

// The specs live at repo-root tests/e2e/** (per the session contract) but their deps
// (@playwright/test, @axe-core/playwright) are installed under webui/node_modules
// (pnpm-isolated). Extend Node's module search path so the specs resolve them.
// (Playwright loads this config from the webui package dir, so cwd is webui.)
const webuiNodeModules = path.join(process.cwd(), "node_modules");
process.env.NODE_PATH = [webuiNodeModules, process.env.NODE_PATH]
  .filter(Boolean)
  .join(path.delimiter);
(Module as unknown as { _initPaths: () => void })._initPaths();

// E2E gate for the Actions shell: gallery a11y (axe), keyboard nav, the same-origin
// BFF proxy (INV-1), and SSE round-trip/reconnect — all against a hermetic Node stub
// upstream (no GPU/api). `serve.mjs` boots the stub + the dev server wired to it.
const PORT = Number(process.env.E2E_PORT ?? 3100);

export default defineConfig({
  testDir: "../tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "node tests/e2e/serve.mjs",
    url: `http://127.0.0.1:${PORT}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    cwd: "..",
  },
});
