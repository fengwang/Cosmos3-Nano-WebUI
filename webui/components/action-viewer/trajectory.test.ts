import { describe, expect, it } from "vitest";

import { parseTrajectory, TrajectoryParseError } from "./trajectory";

const make = (T: number, width: number): number[][] =>
  Array.from({ length: T }, (_, t) => Array.from({ length: width }, (_, d) => t * 0.1 + d * 0.01));

describe("parseTrajectory", () => {
  it("parses a well-formed [16][29] trajectory", () => {
    const r = parseTrajectory(make(16, 29));
    expect(r.T).toBe(16);
    expect(r.width).toBe(29);
    expect(r.frames).toHaveLength(16);
  });

  it("parses a [60][9] av trajectory", () => {
    const r = parseTrajectory(make(60, 9));
    expect(r).toMatchObject({ T: 60, width: 9 });
  });

  it("rejects an empty payload", () => {
    expect(() => parseTrajectory([])).toThrow(TrajectoryParseError);
    expect(() => parseTrajectory(null)).toThrow(TrajectoryParseError);
  });

  it("rejects a ragged (non-rectangular) payload", () => {
    expect(() => parseTrajectory([[1, 2, 3], [1, 2]])).toThrow(/ragged/);
  });

  it("rejects a non-numeric / NaN cell", () => {
    expect(() => parseTrajectory([[1, 2], [3, "x" as unknown as number]])).toThrow(/non-numeric/);
    expect(() => parseTrajectory([[1, 2], [3, NaN]])).toThrow(/non-numeric/);
  });
});
