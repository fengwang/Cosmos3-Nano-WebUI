import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Unit test runner for the pure core (Calculations) + component behavior.
// jsdom for React Testing Library; the `@/` alias mirrors tsconfig paths.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: /^@\//, replacement: fileURLToPath(new URL("./", import.meta.url)) },
    ],
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    include: [
      "design-system/**/*.test.{ts,tsx}",
      "lib/**/*.test.{ts,tsx}",
      "app/**/*.test.{ts,tsx}", // UX-S3: run route/nav specs co-located under app/
      "components/**/*.test.{ts,tsx}", // UX-S3: broadened from action-viewer to all components (incl. S10 pure-core)
    ],
    css: false,
  },
});
