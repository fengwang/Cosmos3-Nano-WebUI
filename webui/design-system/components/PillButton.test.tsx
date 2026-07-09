import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PillButton } from "@/design-system/components/PillButton";

describe("PillButton", () => {
  it("renders an accessible button with its label", () => {
    render(<PillButton>Run</PillButton>);
    expect(screen.getByRole("button", { name: "Run" })).toBeInTheDocument();
  });

  it("activates via the keyboard (Enter and Space)", async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<PillButton onClick={onClick}>Go</PillButton>);

    await user.tab();
    expect(screen.getByRole("button", { name: "Go" })).toHaveFocus();
    await user.keyboard("{Enter}");
    await user.keyboard(" ");
    expect(onClick).toHaveBeenCalledTimes(2);
  });

  it("does not activate when disabled", async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(
      <PillButton disabled onClick={onClick}>
        Nope
      </PillButton>,
    );
    const btn = screen.getByRole("button", { name: "Nope" });
    expect(btn).toBeDisabled();
    await user.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("marks the selected state with aria-pressed (a non-color signal)", () => {
    render(
      <PillButton selected aria-label="Filter">
        Filter
      </PillButton>,
    );
    expect(screen.getByRole("button", { name: "Filter" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});
