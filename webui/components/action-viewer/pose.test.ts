import { describe, expect, it } from "vitest";

import { eulerToQuat, lerp, normalizeQuat, slerpQuat } from "./interpolate";
import type { Quat } from "./interpolate";
import { EMBODIMENT_JOINT_MAPS } from "./jointmap";
import { buildPose } from "./pose";

const agibot = EMBODIMENT_JOINT_MAPS.agibotworld;
const q1 = eulerToQuat(0, 0, 1.0);

// Two 29-wide frames: frame a is zero pose + identity chest quat; frame b drives a couple of joints + a
// rotated chest quat (dims 25-28).
const a = Array(29).fill(0);
a[28] = 1; // identity quaternion (w=1)
const b = Array(29).fill(0);
b[0] = 1.0; // l_shoulder_pitch
b[8] = 0.5; // r_shoulder_pitch
b[25] = q1.x; b[26] = q1.y; b[27] = q1.z; b[28] = q1.w;
const frames = [a, b];

const norm = (q: { x: number; y: number; z: number; w: number }) => Math.hypot(q.x, q.y, q.z, q.w);

describe("buildPose", () => {
  it("LERPs scalar joints at the midpoint", () => {
    const pose = buildPose(frames, agibot, { i0: 0, i1: 1, frac: 0.5 });
    expect(pose.joints.l_shoulder_pitch).toBeCloseTo(0.5, 10);
    expect(pose.joints.r_shoulder_pitch).toBeCloseTo(0.25, 10);
    expect(pose.joints.l_elbow).toBeCloseTo(0, 10);
  });

  it("SLERPs the chest orientation group to a unit quaternion on the named link", () => {
    const pose = buildPose(frames, agibot, { i0: 0, i1: 1, frac: 0.5 });
    expect(pose.orientations).toHaveLength(1);
    expect(pose.orientations[0].link).toBe("chest");
    expect(norm(pose.orientations[0].quat)).toBeCloseTo(1, 10);
  });

  it("returns the i0 frame exactly when frac is 0", () => {
    const pose = buildPose(frames, agibot, { i0: 0, i1: 1, frac: 0 });
    expect(pose.joints.l_shoulder_pitch).toBe(0);
    // identity quaternion (normalized)
    expect(pose.orientations[0].quat.w).toBeCloseTo(1, 10);
    expect(pose.orientations[0].quat.z).toBeCloseTo(0, 10);
  });

  it("covers every mapped scalar joint", () => {
    const pose = buildPose(frames, agibot, { i0: 0, i1: 1, frac: 0.5 });
    expect(Object.keys(pose.joints)).toHaveLength(agibot.joints.length); // 25 scalar joints
  });

  it("SLERPs the orientation group (NOT a component lerp) — guards a slerp→lerp swap at the pose layer", () => {
    const q0 = eulerToQuat(0, 0, 0);
    const q1 = eulerToQuat(1.2, 0.9, 1.5); // a compound (multi-axis) rotation where slerp ≠ nlerp
    const fa = Array(29).fill(0);
    fa[25] = q0.x; fa[26] = q0.y; fa[27] = q0.z; fa[28] = q0.w;
    const fb = Array(29).fill(0);
    fb[25] = q1.x; fb[26] = q1.y; fb[27] = q1.z; fb[28] = q1.w;
    // Sample at t=0.25 — SLERP and normalized-lerp coincide at the midpoint t=0.5 by symmetry, so use a
    // quarter point where they genuinely diverge for a wide rotation.
    const t = 0.25;
    const out = buildPose([fa, fb], agibot, { i0: 0, i1: 1, frac: t }).orientations[0].quat;
    const maxDiff = (a: Quat, b: Quat) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y), Math.abs(a.z - b.z), Math.abs(a.w - b.w));
    // It equals the canonical SLERP…
    expect(maxDiff(out, slerpQuat(q0, q1, t))).toBeLessThan(1e-9);
    // …and is measurably different from a naive normalized component-lerp (what a slerp→lerp swap would give).
    const nlerp = normalizeQuat({ x: lerp(q0.x, q1.x, t), y: lerp(q0.y, q1.y, t), z: lerp(q0.z, q1.z, t), w: lerp(q0.w, q1.w, t) });
    expect(maxDiff(out, nlerp)).toBeGreaterThan(1e-3);
  });
});
