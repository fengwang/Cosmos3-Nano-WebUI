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
      "components/action-viewer/**/*.test.{ts,tsx}", // S10 pure-core Calculations co-located with the viewer
    ],
    css: false,
  },
});
