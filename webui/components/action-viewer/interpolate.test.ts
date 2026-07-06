import { describe, expect, it } from "vitest";

import { eulerToQuat, lerp, normalizeQuat, slerpQuat } from "./interpolate";
import type { Quat } from "./interpolate";

const norm = (q: Quat) => Math.hypot(q.x, q.y, q.z, q.w);
const negate = (q: Quat): Quat => ({ x: -q.x, y: -q.y, z: -q.z, w: -q.w });
const maxDiff = (a: Quat, b: Quat) =>
  Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y), Math.abs(a.z - b.z), Math.abs(a.w - b.w));

describe("lerp (scalar joints)", () => {
  it("is exact at the endpoints and linear at the midpoint", () => {
    expect(lerp(0, 1, 0.5)).toBe(0.5);
    expect(lerp(2, 4, 0)).toBe(2);
    expect(lerp(2, 4, 1)).toBe(4);
    expect(lerp(-1, 1, 0.25)).toBeCloseTo(-0.5, 12);
  });
});

describe("slerpQuat (orientation groups)", () => {
  it("returns the same orientation when both inputs are equal", () => {
    const q = normalizeQuat({ x: 0.1, y: 0.2, z: 0.3, w: 0.9 });
    expect(maxDiff(slerpQuat(q, q, 0.5), q)).toBeLessThan(1e-9);
  });

  it("stays unit-norm across the interval", () => {
    const q0 = eulerToQuat(0, 0, 0);
    const q1 = eulerToQuat(1.2, -0.8, 1.5);
    for (const t of [0, 0.25, 0.5, 0.75, 1]) {
      expect(norm(slerpQuat(q0, q1, t))).toBeCloseTo(1, 10);
    }
  });

  it("takes the shortest arc (sign of the antipodal quaternion is irrelevant)", () => {
    const q0 = eulerToQuat(0, 0, 0.1);
    const q1 = eulerToQuat(0, 0, 0.2);
    const viaPositive = slerpQuat(q0, q1, 0.5);
    const viaNegated = slerpQuat(q0, negate(q1), 0.5); // antipodal → must give the same shortest-arc result
    expect(maxDiff(viaPositive, viaNegated)).toBeLessThan(1e-9);
  });

  it("differs from a naive per-Euler-angle lerp for a compound rotation (SLERP ≠ linear)", () => {
    const q0 = eulerToQuat(0, 0, 0);
    const q1 = eulerToQuat(1.2, 1.2, 1.2);
    const slerpMid = slerpQuat(q0, q1, 0.5);
    const eulerLerpMid = eulerToQuat(0.6, 0.6, 0.6); // what you'd (wrongly) get lerping the angles
    expect(maxDiff(slerpMid, eulerLerpMid)).toBeGreaterThan(1e-3);
    expect(norm(slerpMid)).toBeCloseTo(1, 10);
  });
});

describe("normalizeQuat", () => {
  it("scales to unit norm and guards the zero quaternion", () => {
    expect(norm(normalizeQuat({ x: 0, y: 3, z: 0, w: 4 }))).toBeCloseTo(1, 12);
    expect(normalizeQuat({ x: 0, y: 0, z: 0, w: 0 })).toEqual({ x: 0, y: 0, z: 0, w: 1 });
  });
});
