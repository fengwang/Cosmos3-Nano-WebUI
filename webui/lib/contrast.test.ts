import { describe, expect, it } from "vitest";

import { contrastRatio, hexToRgb, relLuminance } from "@/lib/contrast";

// Reference values from the WCAG 2.x relative-luminance + contrast formulas.
describe("hexToRgb", () => {
  it("parses 6-digit hex (with or without #)", () => {
    expect(hexToRgb("#ffffff")).toEqual([255, 255, 255]);
    expect(hexToRgb("000000")).toEqual([0, 0, 0]);
    expect(hexToRgb("#1e2632")).toEqual([30, 38, 50]);
  });
});

describe("relLuminance", () => {
  it("is 1 for white and 0 for black", () => {
    expect(relLuminance([255, 255, 255])).toBeCloseTo(1, 5);
    expect(relLuminance([0, 0, 0])).toBeCloseTo(0, 5);
  });
});

describe("contrastRatio", () => {
  it("is exactly 21 for black on white", () => {
    expect(contrastRatio([255, 255, 255], [0, 0, 0])).toBeCloseTo(21, 5);
  });

  it("is 1 for identical colors", () => {
    expect(contrastRatio([30, 38, 50], [30, 38, 50])).toBeCloseTo(1, 5);
  });

  it("is symmetric (order-independent)", () => {
    const a: [number, number, number] = [230, 234, 240];
    const b: [number, number, number] = [30, 38, 50];
    expect(contrastRatio(a, b)).toBeCloseTo(contrastRatio(b, a), 10);
  });

  it("matches the canonical AA boundary gray #767676 on white (~4.54)", () => {
    expect(contrastRatio(hexToRgb("#767676"), hexToRgb("#ffffff"))).toBeCloseTo(4.54, 1);
  });
});
