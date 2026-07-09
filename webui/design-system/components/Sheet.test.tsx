import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { Sheet } from "@/design-system/components/Sheet";

function Harness() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button onClick={() => setOpen(true)}>Open</button>
      <Sheet open={open} onClose={() => setOpen(false)} title="Settings">
        <button>Save</button>
      </Sheet>
    </>
  );
}

describe("Sheet", () => {
  it("is a modal dialog that takes focus, closes on Escape, and returns focus", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.click(screen.getByRole("button", { name: "Open" }));
    const dialog = screen.getByRole("dialog", { name: "Settings" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    // Focus moved into the dialog (the first focusable is Save).
    expect(screen.getByRole("button", { name: "Save" })).toHaveFocus();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    // Focus returned to the trigger.
    expect(screen.getByRole("button", { name: "Open" })).toHaveFocus();
  });

  it("renders nothing when closed", () => {
    render(
      <Sheet open={false} onClose={() => {}} title="Hidden">
        <p>body</p>
      </Sheet>,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
