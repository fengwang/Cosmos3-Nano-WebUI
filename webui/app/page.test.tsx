import { describe, expect, it, vi } from "vitest";
import { redirect } from "next/navigation";

// Home is a server component whose sole effect is a redirect; mock the framework
// control function so the call is observable instead of throwing.
vi.mock("next/navigation", () => ({ redirect: vi.fn() }));

import Home from "./page";

describe("Home route", () => {
  it("redirects to the Studio and renders nothing (no dead link)", () => {
    const rendered = Home();
    expect(redirect).toHaveBeenCalledWith("/studio");
    // Its only effect is the redirect: no JSX is returned, so no dead link can
    // render at `/`. A regression returning markup alongside the redirect would
    // make this defined.
    expect(rendered).toBeUndefined();
  });
});
