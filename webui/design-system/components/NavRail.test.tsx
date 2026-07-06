import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { NavRail } from "@/design-system/components/NavRail";

const ITEMS = [
  { href: "/compose", label: "Compose" },
  { href: "/run", label: "Run" },
];

describe("NavRail", () => {
  it("exposes a labelled navigation landmark", () => {
    render(<NavRail currentPath="/" items={[{ href: "/", label: "Home" }]} />);
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
  });

  it("gives every item an accessible name and marks the current route", () => {
    render(<NavRail currentPath="/run" items={ITEMS} />);
    expect(screen.getByRole("link", { name: "Run" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Compose" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
