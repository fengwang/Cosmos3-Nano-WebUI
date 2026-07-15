import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// PrimaryNav reads the active route via usePathname; pin it so the pure NavRail renders.
vi.mock("next/navigation", () => ({ usePathname: () => "/studio" }));

import { PrimaryNav } from "./PrimaryNav";

// The rail is exactly Studio / Reasoning / Action / History. Asserting the full,
// ordered set guards against re-adding a removed developer route without naming
// it, so the repo-wide route-name sweep stays clean.
describe("PrimaryNav", () => {
  it("renders exactly the four work-area labels in order", () => {
    render(<PrimaryNav />);
    const labels = screen.getAllByRole("link").map((a) => a.textContent);
    expect(labels).toEqual(["Studio", "Reasoning", "Action", "History"]);
  });

  it("exposes exactly the four work-area routes in order", () => {
    const { container } = render(<PrimaryNav />);
    const hrefs = Array.from(container.querySelectorAll("a")).map((a) => a.getAttribute("href"));
    expect(hrefs).toEqual(["/studio", "/chat", "/action", "/history"]);
  });
});
