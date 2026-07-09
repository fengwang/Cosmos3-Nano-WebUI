import { describe, expect, it } from "vitest";

import { decideViewer } from "./viewerDecision";
import type { ViewerInputs } from "./viewerDecision";

const base: ViewerInputs = {
  domain: "agibotworld",
  hasTrajectory: true,
  trajectoryWidth: 29,
  canonicalWidth: 29,
  mode: "3d",
  hasMap: true,
  hasUrdf: true,
  configError: null,
  viewerError: null,
};

describe("decideViewer (3D-vs-fallback gate — INV-6/RK-12/RK-04)", () => {
  it("shows 3D for a fully-valid verified embodiment", () => {
    expect(decideViewer(base)).toEqual({ show3D: true, reason: null });
  });

  it("no trajectory → no view, no reason banner", () => {
    expect(decideViewer({ ...base, hasTrajectory: false })).toEqual({ show3D: false, reason: null });
  });

  it("fallback-routed embodiment (av) → 2D-only with a routing reason (no misleading 3D)", () => {
    const d = decideViewer({ ...base, domain: "av", mode: "fallback", trajectoryWidth: 9, canonicalWidth: 9 });
    expect(d.show3D).toBe(false);
    expect(d.reason).toMatch(/not a verified 3D embodiment/i);
  });

  it("verified embodiment but INVALID joint-map (configError) → refuse 3D (the silent-dim-mismatch guard)", () => {
    const d = decideViewer({
      ...base,
      configError: { code: "DIM_MISMATCH", message: "joint-map covers 28 dims but embodiment width is 29", expected: 29, got: 28 },
    });
    expect(d.show3D).toBe(false);
    expect(d.reason).toContain("28 dims");
  });

  it("trajectory DATA width mismatch → refuse 3D and surface it (not silently zero-filled)", () => {
    const d = decideViewer({ ...base, trajectoryWidth: 28 });
    expect(d.show3D).toBe(false);
    expect(d.reason).toMatch(/width 28 does not match the expected 29/i);
  });

  it("missing map or URDF → fallback", () => {
    expect(decideViewer({ ...base, hasMap: false }).show3D).toBe(false);
    expect(decideViewer({ ...base, hasUrdf: false }).show3D).toBe(false);
  });

  it("runtime viewer error (WebGL unavailable) → fallback with the error reason", () => {
    const d = decideViewer({ ...base, viewerError: "WebGL is unavailable in this browser." });
    expect(d.show3D).toBe(false);
    expect(d.reason).toContain("WebGL is unavailable");
  });
});
