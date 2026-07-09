import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Card } from "@/design-system/components/Card";

describe("Card", () => {
  it("is a labelled region when given a title", () => {
    render(<Card title="Occupancy">body</Card>);
    expect(screen.getByRole("region", { name: "Occupancy" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Occupancy" })).toBeInTheDocument();
    expect(screen.getByText("body")).toBeInTheDocument();
  });

  it("renders children without a title", () => {
    render(<Card>plain</Card>);
    expect(screen.getByText("plain")).toBeInTheDocument();
  });
});
