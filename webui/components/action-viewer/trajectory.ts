// Trajectory parsing (ACD: pure Calculation). The api serves the trajectory as a bare `number[][]` of
// shape [T][raw_dim] (api/jobs/artifacts.py:write_trajectory_json) — no wrapper, no fps. We validate the
// shape so a malformed payload becomes a typed error the UI surfaces, never NaN joints in the scene.

export interface ParsedTrajectory {
  frames: number[][];
  T: number;
  width: number;
}

export class TrajectoryParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TrajectoryParseError";
  }
}

/**
 * Pure: parse + validate a `number[][]` trajectory. Throws `TrajectoryParseError` on an empty, ragged
 * (non-rectangular), or non-numeric payload (never returns NaN cells).
 */
export function parseTrajectory(raw: unknown): ParsedTrajectory {
  if (!Array.isArray(raw) || raw.length === 0) {
    throw new TrajectoryParseError("trajectory must be a non-empty array of frames");
  }
  const first = raw[0];
  if (!Array.isArray(first) || first.length === 0) {
    throw new TrajectoryParseError("trajectory frames must be non-empty arrays");
  }
  const width = first.length;
  for (let t = 0; t < raw.length; t++) {
    const row = raw[t];
    if (!Array.isArray(row) || row.length !== width) {
      throw new TrajectoryParseError(`trajectory is ragged: frame ${t} has length ${Array.isArray(row) ? row.length : "n/a"}, expected ${width}`);
    }
    for (let d = 0; d < width; d++) {
      if (typeof row[d] !== "number" || Number.isNaN(row[d])) {
        throw new TrajectoryParseError(`trajectory has a non-numeric value at frame ${t}, dim ${d}`);
      }
    }
  }
  return { frames: raw as number[][], T: raw.length, width };
}
