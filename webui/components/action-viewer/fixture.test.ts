import { describe, expect, it } from "vitest";

import { demoTrajectory } from "./fixture";

describe("demoTrajectory", () => {
  it("produces a [T][width] trajectory", () => {
    const traj = demoTrajectory(29, 16, [25, 26, 27, 28]);
    expect(traj).toHaveLength(16);
    expect(traj.every((row) => row.length === 29)).toBe(true);
  });

  it("fills the quaternion dims with a unit quaternion", () => {
    const traj = demoTrajectory(29, 16, [25, 26, 27, 28]);
    for (const row of traj) {
      const n = Math.hypot(row[25], row[26], row[27], row[28]);
      expect(n).toBeCloseTo(1, 10);
    }
  });

  it("works for a vehicle width with no orientation group", () => {
    const traj = demoTrajectory(9, 60);
    expect(traj).toHaveLength(60);
    expect(traj[0]).toHaveLength(9);
  });

  it("is deterministic", () => {
    expect(demoTrajectory(9, 4)).toEqual(demoTrajectory(9, 4));
  });
});
