// Pose building (ACD: pure Calculation). Given a parsed trajectory, a joint-map, and a bracketing sample,
// produce the joint angles + orientation quaternions to apply to the URDF. Scalar joints are LERP'd;
// orientation groups are SLERP'd. Keeping this pure makes the risky dim→pose step DOM-free unit-testable;
// the URDFScene seam only *applies* the result. Refs: design D5/D8.

import { lerp, slerpQuat } from "./interpolate";
import type { Quat } from "./interpolate";
import type { JointMap } from "./jointmap";
import type { Sample } from "./sync";

export interface Pose {
  /** jointName → angle/position (scalar joints). */
  joints: Record<string, number>;
  /** orientation groups → the quaternion to apply to the named link. */
  orientations: { link: string; quat: Quat }[];
}

/**
 * Pure: interpolate the pose at a bracketing sample. Scalar joints are linearly interpolated between the
 * two frames; orientation groups are SLERP'd. Missing cells default to 0 (and w→1 for the quaternion's
 * scalar part) so a short row never yields a NaN joint.
 */
export function buildPose(frames: number[][], map: JointMap, s: Sample): Pose {
  const a = frames[s.i0] ?? [];
  const b = frames[s.i1] ?? a;
  const joints: Record<string, number> = {};
  for (const j of map.joints) {
    joints[j.joint] = lerp(a[j.dim] ?? 0, b[j.dim] ?? 0, s.frac);
  }
  const orientations = (map.orientation ?? []).map((g) => {
    const [ix, iy, iz, iw] = g.dims;
    const q0: Quat = { x: a[ix] ?? 0, y: a[iy] ?? 0, z: a[iz] ?? 0, w: a[iw] ?? 1 };
    const q1: Quat = { x: b[ix] ?? 0, y: b[iy] ?? 0, z: b[iz] ?? 0, w: b[iw] ?? 1 };
    return { link: g.link, quat: slerpQuat(q0, q1, s.frac) };
  });
  return { joints, orientations };
}
