// EMBODIMENT → {dim → joint} mapping + schema validation (ACD: inert Data + a pure Calculation).
//
// ⚠️ The dim→joint layout below is a DECLARED CANDIDATE CONVENTION authored in-repo for visualization. The
// action engine's TRUE per-dimension semantics for `agibotworld` are undocumented (the engine tables record
// only the width, 29). It is NOT asserted to be ground truth — it is structurally validated (dim count,
// contiguous coverage, joint existence), gated by the human visual gate (EC-U3), and the 2D trajectory plot
// is the always-correct floor. See `webui/public/urdf/PROVENANCE.md`. Refs: design D4; INV-6; RK-04/RK-12.

/** A scalar joint driven by one trajectory dimension. */
export interface JointEntry {
  dim: number;
  joint: string;
  kind: "revolute" | "continuous" | "prismatic";
}

/** A multi-dim orientation applied to a link as a quaternion (the SLERP path). `dims` are (x,y,z,w). */
export interface OrientationGroup {
  /** Exactly the 4 trajectory dims forming the orientation quaternion (x, y, z, w). */
  dims: [number, number, number, number];
  link: string;
}

export interface JointMap {
  domain: string;
  /** Human-readable note that this is a candidate convention, not ground truth (RK-04). */
  convention: string;
  joints: JointEntry[];
  orientation?: OrientationGroup[];
}

export type JointMapErrorCode = "DIM_MISMATCH" | "BAD_COVERAGE" | "UNKNOWN_JOINT";

export interface JointMapError {
  code: JointMapErrorCode;
  message: string;
  expected?: number;
  got?: number;
}

const CANDIDATE = "CANDIDATE convention — authored in-repo; gated by the human visual gate; NOT the engine's ground-truth layout";

/** All trajectory dims a map covers (scalar joints + orientation-group dims), in declared order. */
export function mappedDims(map: JointMap): number[] {
  return [...map.joints.map((j) => j.dim), ...(map.orientation ?? []).flatMap((o) => o.dims)];
}

/**
 * Pure Calculation: validate a joint-map against the embodiment schema. Returns `null` (Ok) or a typed
 * error. Ok ONLY when (a) the mapped dim count equals the canonical `width` (no silent mismatch — INV-6),
 * (b) the dims are a contiguous `0..width-1` permutation (no gaps/dupes), and (c) every scalar joint exists
 * in `urdfJointNames`. The orientation group references a *link* (validated at the scene seam), not a joint.
 */
export function validateJointMap(map: JointMap, width: number, urdfJointNames: string[]): JointMapError | null {
  const dims = mappedDims(map);
  if (dims.length !== width) {
    return {
      code: "DIM_MISMATCH",
      message: `joint-map covers ${dims.length} dims but embodiment width is ${width}`,
      expected: width,
      got: dims.length,
    };
  }
  const sorted = [...dims].sort((a, b) => a - b);
  for (let i = 0; i < sorted.length; i++) {
    if (sorted[i] !== i) {
      return {
        code: "BAD_COVERAGE",
        message: `dims must be a contiguous 0..${width - 1} permutation (no gaps/duplicates); got ${JSON.stringify(sorted)}`,
      };
    }
  }
  const known = new Set(urdfJointNames);
  const missing = map.joints.find((j) => !known.has(j.joint));
  if (missing) {
    return { code: "UNKNOWN_JOINT", message: `mapped joint "${missing.joint}" is not present in the URDF` };
  }
  return null;
}

/**
 * The agibotworld candidate convention (29-D): 25 scalar joints (dims 0–24) + a 4-dim chest-orientation
 * quaternion (dims 25–28). The joint names match `webui/public/urdf/agibotworld.urdf`.
 */
export const EMBODIMENT_JOINT_MAPS: Record<string, JointMap> = {
  agibotworld: {
    domain: "agibotworld",
    convention: CANDIDATE,
    joints: [
      { dim: 0, joint: "l_shoulder_pitch", kind: "revolute" },
      { dim: 1, joint: "l_shoulder_roll", kind: "revolute" },
      { dim: 2, joint: "l_shoulder_yaw", kind: "revolute" },
      { dim: 3, joint: "l_elbow", kind: "revolute" },
      { dim: 4, joint: "l_wrist_pitch", kind: "revolute" },
      { dim: 5, joint: "l_wrist_roll", kind: "revolute" },
      { dim: 6, joint: "l_wrist_yaw", kind: "revolute" },
      { dim: 7, joint: "l_gripper", kind: "prismatic" },
      { dim: 8, joint: "r_shoulder_pitch", kind: "revolute" },
      { dim: 9, joint: "r_shoulder_roll", kind: "revolute" },
      { dim: 10, joint: "r_shoulder_yaw", kind: "revolute" },
      { dim: 11, joint: "r_elbow", kind: "revolute" },
      { dim: 12, joint: "r_wrist_pitch", kind: "revolute" },
      { dim: 13, joint: "r_wrist_roll", kind: "revolute" },
      { dim: 14, joint: "r_wrist_yaw", kind: "revolute" },
      { dim: 15, joint: "r_gripper", kind: "prismatic" },
      { dim: 16, joint: "waist_yaw", kind: "revolute" },
      { dim: 17, joint: "waist_pitch", kind: "revolute" },
      { dim: 18, joint: "waist_roll", kind: "revolute" },
      { dim: 19, joint: "head_yaw", kind: "revolute" },
      { dim: 20, joint: "head_pitch", kind: "revolute" },
      { dim: 21, joint: "body_lift", kind: "prismatic" },
      { dim: 22, joint: "base_x", kind: "prismatic" },
      { dim: 23, joint: "base_y", kind: "prismatic" },
      { dim: 24, joint: "base_yaw", kind: "continuous" },
    ],
    orientation: [{ dims: [25, 26, 27, 28], link: "chest" }],
  },
};
