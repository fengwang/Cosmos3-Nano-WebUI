import { describe, expect, it } from "vitest";

import { dimSeries, plotPath, toPolylinePoints } from "./plot";

describe("plotPath", () => {
  it("maps a series to T points within the viewport", () => {
    const pts = plotPath([0, 1, 2, 3, 4], 100, 50);
    expect(pts).toHaveLength(5);
    for (const p of pts) {
      expect(p.x).toBeGreaterThanOrEqual(0);
      expect(p.x).toBeLessThanOrEqual(100);
      expect(p.y).toBeGreaterThanOrEqual(0);
      expect(p.y).toBeLessThanOrEqual(50);
    }
    expect(pts[0].x).toBe(0);
    expect(pts[4].x).toBe(100);
    expect(pts[4].y).toBe(0); // the max value sits at the top (y=0)
    expect(pts[0].y).toBe(50); // the min at the bottom
  });

  it("renders a constant series as a horizontal midline", () => {
    const pts = plotPath([3, 3, 3, 3], 80, 40);
    const ys = pts.map((p) => p.y);
    expect(new Set(ys).size).toBe(1); // all equal
    expect(ys[0]).toBeCloseTo(20, 6); // midline
  });

  it("places a single-sample series at the left midline", () => {
    expect(plotPath([7], 100, 50)).toEqual([{ x: 0, y: 25 }]);
  });

  it("returns no points for an empty series", () => {
    expect(plotPath([], 100, 50)).toEqual([]);
  });
});

describe("dimSeries", () => {
  it("extracts one dimension across frames", () => {
    const frames = [
      [1, 2, 3],
      [4, 5, 6],
    ];
    expect(dimSeries(frames, 0)).toEqual([1, 4]);
    expect(dimSeries(frames, 2)).toEqual([3, 6]);
  });
});

describe("toPolylinePoints", () => {
  it("formats points as an SVG points string", () => {
    expect(toPolylinePoints([{ x: 0, y: 10 }, { x: 5.5, y: 2.25 }])).toBe("0.00,10.00 5.50,2.25");
  });
});
