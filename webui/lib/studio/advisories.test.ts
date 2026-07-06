import { describe, expect, it } from "vitest";

import { advisoriesFor } from "@/lib/studio/advisories";
import type { Draft } from "@/lib/studio/types";

function draft(params: Draft["params"]): Draft {
  return { mode: "t2v", prompt: "p", preset: "standard-480", params };
}

describe("advisoriesFor", () => {
  it("advises on 720p (RK-08 high-res envelope)", () => {
    const w = advisoriesFor(draft({ height: 720, width: 1280 }));
    expect(w.map((x) => x.code)).toContain("hi_res_envelope");
  });

  it("advises on 960p portrait (height >= 720)", () => {
    const w = advisoriesFor(draft({ height: 960, width: 720 }));
    expect(w.map((x) => x.code)).toContain("hi_res_envelope");
  });

  it("does not advise on 480p", () => {
    expect(advisoriesFor(draft({ height: 480, width: 640 }))).toEqual([]);
  });

  it("advises on long frame counts", () => {
    expect(advisoriesFor(draft({ height: 480, width: 640, num_frames: 200 })).map((x) => x.code)).toContain("long_frames");
  });

  it("only ever emits non-blocking severities (never error)", () => {
    const w = advisoriesFor(draft({ height: 720, width: 1280, num_frames: 400 }));
    expect(w.every((x) => x.severity !== "error")).toBe(true);
  });
});
