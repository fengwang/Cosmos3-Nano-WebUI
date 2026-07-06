// 2D trajectory-plot geometry (ACD: pure Calculation). Maps a [T]-length per-dimension series to SVG path
// points within a `w×h` viewport, auto-scaled to the series' min/max; a flat series maps to a horizontal
// midline. This is the GUARANTEED FLOOR (it makes no semantic claim about the dims). Refs: design D7.

export interface Point {
  x: number;
  y: number;
}

/**
 * Pure: project a numeric series onto `w×h` SVG coordinates. The first sample is at x=0, the last at x=w
 * (SVG y grows downward, so the largest value sits at y=0). A constant series → a horizontal midline. A
 * single-sample series → one point at (0, h/2). All points lie within `[0,w]×[0,h]`.
 */
export function plotPath(series: number[], w: number, h: number): Point[] {
  const n = series.length;
  if (n === 0) return [];
  let lo = Math.min(...series);
  let hi = Math.max(...series);
  if (hi === lo) {
    // Flat series: center it on a midline (avoids divide-by-zero and a degenerate scale).
    hi = lo + 1;
    lo = lo - 1;
  }
  const span = hi - lo;
  return series.map((v, i) => ({
    x: n === 1 ? 0 : (i / (n - 1)) * w,
    y: h - ((v - lo) / span) * h,
  }));
}

/** Pure: an SVG `points` string for a `<polyline>` from plot points. */
export function toPolylinePoints(points: Point[]): string {
  return points.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(" ");
}

/** Pure: extract one dimension's series across all frames. */
export function dimSeries(frames: number[][], dim: number): number[] {
  return frames.map((f) => f[dim] ?? 0);
}
