import { describe, expect, it } from "vitest";

import { currentFrame, normalizedTime, sampleIndex } from "./sync";

describe("sampleIndex (normalized video-master timeline)", () => {
  it("maps the endpoints and a frame-aligned midpoint (T=5)", () => {
    expect(sampleIndex(0, 5)).toEqual({ i0: 0, i1: 0, frac: 0 });
    expect(sampleIndex(1, 5)).toEqual({ i0: 4, i1: 4, frac: 0 });
    expect(sampleIndex(0.5, 5)).toEqual({ i0: 2, i1: 2, frac: 0 });
  });

  it("brackets a between-frames position", () => {
    const s = sampleIndex(0.6, 5); // f = 2.4
    expect(s.i0).toBe(2);
    expect(s.i1).toBe(3);
    expect(s.frac).toBeCloseTo(0.4, 10);
  });

  it("clamps out-of-range time", () => {
    expect(sampleIndex(-0.5, 5)).toEqual({ i0: 0, i1: 0, frac: 0 });
    expect(sampleIndex(1.5, 5)).toEqual({ i0: 4, i1: 4, frac: 0 });
  });

  it("collapses a degenerate single-frame trajectory", () => {
    expect(sampleIndex(0.7, 1)).toEqual({ i0: 0, i1: 0, frac: 0 });
  });
});

describe("normalizedTime", () => {
  it("divides currentTime by duration, clamped", () => {
    expect(normalizedTime(5, 10)).toBe(0.5);
    expect(normalizedTime(20, 10)).toBe(1);
  });
  it("guards a zero/NaN duration", () => {
    expect(normalizedTime(5, 0)).toBe(0);
    expect(normalizedTime(5, NaN)).toBe(0);
  });
});

describe("currentFrame", () => {
  it("rounds the normalized time to a frame index", () => {
    expect(currentFrame(0.5, 5)).toBe(2);
    expect(currentFrame(1, 5)).toBe(4);
    expect(currentFrame(0, 5)).toBe(0);
  });
});
