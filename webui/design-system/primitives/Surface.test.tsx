import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Surface } from "@/design-system/primitives/Surface";

describe("Surface", () => {
  it("renders its children", () => {
    render(<Surface>hi</Surface>);
    expect(screen.getByText("hi")).toBeInTheDocument();
  });

  it("is raised by default and inset on request (exposed via data-variant)", () => {
    const { rerender } = render(<Surface>x</Surface>);
    expect(screen.getByText("x")).toHaveAttribute("data-variant", "raised");
    rerender(<Surface variant="inset">x</Surface>);
    expect(screen.getByText("x")).toHaveAttribute("data-variant", "inset");
  });

  it("renders the semantic element given by `as`", () => {
    render(<Surface as="section">sec</Surface>);
    expect(screen.getByText("sec").tagName).toBe("SECTION");
  });
});
