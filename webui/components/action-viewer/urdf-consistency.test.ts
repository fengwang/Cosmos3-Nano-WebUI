// Verifies the authored URDF and the joint-map agree — the deterministic, WebGL-free core of the
// "URDF + meshes load without error for the supported embodiment" smoke (RK-04 config↔asset drift guard).
// Parses the real `webui/public/urdf/agibotworld.urdf` with the jsdom DOMParser and asserts every mapped
// scalar joint + the orientation-group link exist, and the dim count matches the schema width.
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { canonicalWidthOf } from "./embodiments";
import { EMBODIMENT_JOINT_MAPS, mappedDims, validateJointMap } from "./jointmap";

// vitest runs with cwd = the webui package dir.
const urdfText = readFileSync(path.resolve(process.cwd(), "public/urdf/agibotworld.urdf"), "utf8");
const doc = new DOMParser().parseFromString(urdfText, "application/xml");

const jointNames = Array.from(doc.querySelectorAll("joint")).map((j) => j.getAttribute("name") ?? "");
const linkNames = Array.from(doc.querySelectorAll("link")).map((l) => l.getAttribute("name") ?? "");
const agibot = EMBODIMENT_JOINT_MAPS.agibotworld;

describe("authored URDF ↔ joint-map consistency (agibotworld)", () => {
  it("parses without error and declares joints + links", () => {
    expect(doc.querySelector("parsererror")).toBeNull();
    expect(doc.querySelector("robot")?.getAttribute("name")).toBe("agibotworld");
    expect(jointNames.length).toBeGreaterThan(0);
  });

  it("contains every mapped scalar joint", () => {
    for (const j of agibot.joints) {
      expect(jointNames, `URDF must declare joint ${j.joint}`).toContain(j.joint);
    }
  });

  it("contains the orientation-group link(s)", () => {
    for (const g of agibot.orientation ?? []) {
      expect(linkNames, `URDF must declare link ${g.link}`).toContain(g.link);
    }
  });

  it("validates against the schema width with the real URDF joints (29-D, contiguous, all joints present)", () => {
    expect(mappedDims(agibot)).toHaveLength(29);
    expect(validateJointMap(agibot, canonicalWidthOf("agibotworld") ?? 0, jointNames)).toBeNull();
  });
});
