import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { VisuallyHidden } from "@/design-system/primitives/VisuallyHidden";

describe("VisuallyHidden", () => {
  it("keeps its text in the accessibility tree", () => {
    render(<VisuallyHidden>screen reader only</VisuallyHidden>);
    expect(screen.getByText("screen reader only")).toBeInTheDocument();
  });
});
