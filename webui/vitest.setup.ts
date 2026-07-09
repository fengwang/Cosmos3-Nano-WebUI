// Registers jest-dom matchers (toBeInTheDocument, toHaveAttribute, …) on vitest's
// expect, and applies their type augmentation program-wide for `tsc --noEmit`.
import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// `globals: false`, so RTL's auto-cleanup isn't wired to a global afterEach.
// Unmount between tests to keep each render isolated.
afterEach(() => {
  cleanup();
});
