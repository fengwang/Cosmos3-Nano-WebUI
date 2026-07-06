import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProgressRing } from "@/design-system/components/ProgressRing";

describe("ProgressRing", () => {
  it("exposes its progress to assistive tech via the progressbar role", () => {
    render(<ProgressRing value={60} label="Occupancy" />);
    const pb = screen.getByRole("progressbar", { name: "Occupancy" });
    expect(pb).toHaveAttribute("aria-valuenow", "60");
    expect(pb).toHaveAttribute("aria-valuemin", "0");
    expect(pb).toHaveAttribute("aria-valuemax", "100");
  });

  it("renders a visible value label (not a color-only indicator)", () => {
    render(<ProgressRing value={60} label="Occupancy" />);
    expect(screen.getByText("60%")).toBeInTheDocument();
  });

  it("clamps out-of-range values", () => {
    render(<ProgressRing value={140} label="Over" />);
    expect(screen.getByRole("progressbar", { name: "Over" })).toHaveAttribute(
      "aria-valuenow",
      "100",
    );
  });

  it("treats a non-finite value as 0 (no NaN in aria-valuenow)", () => {
    render(<ProgressRing value={Number.NaN} label="Bad" />);
    expect(screen.getByRole("progressbar", { name: "Bad" })).toHaveAttribute(
      "aria-valuenow",
      "0",
    );
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("indeterminate: keeps the progressbar role + label but drops aria-valuenow and the % text", () => {
    render(<ProgressRing indeterminate label="Generation progress" />);
    const pb = screen.getByRole("progressbar", { name: "Generation progress" });
    expect(pb).not.toHaveAttribute("aria-valuenow");
    expect(screen.queryByText(/%/)).toBeNull();
    expect(screen.getByTestId("ring-spinner")).toBeInTheDocument(); // the animated arc actually renders
  });

  it("determinate: does not render the indeterminate spinner arc", () => {
    render(<ProgressRing value={60} label="Occupancy" />);
    expect(screen.queryByTestId("ring-spinner")).toBeNull();
  });

  it("indeterminate ignores any supplied value (still no numeric readout)", () => {
    render(<ProgressRing indeterminate value={40} label="Working" />);
    expect(screen.getByRole("progressbar", { name: "Working" })).not.toHaveAttribute("aria-valuenow");
    expect(screen.queryByText("40%")).toBeNull();
  });
});
