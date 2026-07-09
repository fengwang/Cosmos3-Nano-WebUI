import { describe, expect, it } from "vitest";

import { canonicalWidthOf, viewerModeFor } from "./embodiments";

describe("viewerModeFor", () => {
  it("routes the verified articulated embodiment to 3D", () => {
    expect(viewerModeFor("agibotworld")).toBe("3d");
  });
  it("routes the av vehicle to the 2D fallback (not a joint tree)", () => {
    expect(viewerModeFor("av")).toBe("fallback");
  });
  it("routes any unknown/unverified domain to the fallback", () => {
    expect(viewerModeFor("pusht")).toBe("fallback");
    expect(viewerModeFor("definitely_unknown")).toBe("fallback");
  });
});

describe("canonicalWidthOf", () => {
  it("mirrors the S4 schema widths", () => {
    expect(canonicalWidthOf("agibotworld")).toBe(29);
    expect(canonicalWidthOf("av")).toBe(9);
  });
  it("returns null for an unknown domain", () => {
    expect(canonicalWidthOf("nope")).toBeNull();
  });
});
