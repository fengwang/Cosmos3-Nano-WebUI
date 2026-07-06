import { describe, expect, it } from "vitest";

import { EMBODIMENT_JOINT_MAPS, mappedDims, validateJointMap } from "./jointmap";
import type { JointMap } from "./jointmap";

const agibot = EMBODIMENT_JOINT_MAPS.agibotworld;
const URDF_JOINTS = agibot.joints.map((j) => j.joint); // the 25 scalar joint names

describe("validateJointMap (deterministic-check #1: dim count == embodiment width)", () => {
  it("accepts a complete 29-dim agibotworld map (25 scalar + 4 orientation)", () => {
    expect(mappedDims(agibot)).toHaveLength(29);
    expect(validateJointMap(agibot, 29, URDF_JOINTS)).toBeNull();
  });

  it("rejects an undersized (28-dim) map with DIM_MISMATCH", () => {
    const short: JointMap = { ...agibot, joints: agibot.joints.slice(0, -1) }; // 24 scalar + 4 = 28
    const err = validateJointMap(short, 29, URDF_JOINTS);
    expect(err?.code).toBe("DIM_MISMATCH");
    expect(err?.expected).toBe(29);
    expect(err?.got).toBe(28);
  });

  it("rejects an oversized (30-dim) map with DIM_MISMATCH", () => {
    const long: JointMap = {
      ...agibot,
      joints: [...agibot.joints, { dim: 29, joint: "extra", kind: "revolute" }], // 26 scalar + 4 = 30
    };
    const err = validateJointMap(long, 29, [...URDF_JOINTS, "extra"]);
    expect(err?.code).toBe("DIM_MISMATCH");
    expect(err?.got).toBe(30);
  });

  it("rejects a non-contiguous mapping (gap/dup) with BAD_COVERAGE", () => {
    const gapped: JointMap = {
      ...agibot,
      joints: agibot.joints.map((j) => (j.dim === 24 ? { ...j, dim: 30 } : j)), // count 29, but 24 missing / 30 present
    };
    expect(validateJointMap(gapped, 29, URDF_JOINTS)?.code).toBe("BAD_COVERAGE");
  });

  it("rejects a joint name absent from the URDF with UNKNOWN_JOINT", () => {
    const bogus: JointMap = {
      ...agibot,
      joints: agibot.joints.map((j, i) => (i === 0 ? { ...j, joint: "bogus_joint" } : j)),
    };
    const err = validateJointMap(bogus, 29, URDF_JOINTS);
    expect(err?.code).toBe("UNKNOWN_JOINT");
    expect(err?.message).toContain("bogus_joint");
  });

  it("counts the orientation-group dims toward coverage", () => {
    expect(mappedDims(agibot)).toEqual(expect.arrayContaining([25, 26, 27, 28]));
  });

  it("labels the mapping a candidate convention (RK-04 honesty)", () => {
    expect(agibot.convention).toMatch(/candidate/i);
  });
});
