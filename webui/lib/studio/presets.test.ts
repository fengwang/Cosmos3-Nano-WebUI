import { describe, expect, it } from "vitest";

import { applyPreset, PRESET_LIST, PRESETS, presetParams } from "@/lib/studio/presets";
import type { Draft } from "@/lib/studio/types";

function draft(): Draft {
  return { mode: "t2v", prompt: "p", preset: "standard-480", params: { height: 480, width: 640 } };
}

describe("preset catalog", () => {
  it("only uses valid dimensions and frames within the cap", () => {
    const validDims = [256, 480, 640, 720, 960, 1280];
    for (const p of PRESET_LIST) {
      expect(validDims).toContain(p.params.height);
      expect(validDims).toContain(p.params.width);
      expect(p.params.num_frames ?? 0).toBeLessThanOrEqual(720);
    }
  });
});

describe("presetParams", () => {
  it("returns a fresh copy (mutating it never mutates the catalog)", () => {
    const params = presetParams("standard-480");
    params.height = 999;
    expect(PRESETS["standard-480"].params.height).toBe(480);
  });
});

describe("applyPreset", () => {
  it("sets the preset id and its params deterministically", () => {
    const next = applyPreset(draft(), "standard-480");
    expect(next.preset).toBe("standard-480");
    expect(next.params.height).toBe(480);
    expect(next.params.width).toBe(640);
  });

  it("does not mutate the input draft", () => {
    const original = draft();
    applyPreset(original, "hi-720");
    expect(original.preset).toBe("standard-480");
    expect(original.params.height).toBe(480);
  });
});
