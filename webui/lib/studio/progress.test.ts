import { describe, expect, it } from "vitest";

import { initialJobView } from "@/lib/studio/jobState";
import type { JobView } from "@/lib/studio/jobState";
import { describeProgress } from "@/lib/studio/progress";

const view = (over: Partial<JobView>): JobView => ({ ...initialJobView(), ...over });

describe("describeProgress", () => {
  it("is indeterminate while non-terminal at exactly zero progress (sync/no-progress modes)", () => {
    expect(describeProgress(view({ status: "running", progress: 0, terminal: false })).indeterminate).toBe(true);
  });

  it("treats the queued/pre-progress state as indeterminate", () => {
    expect(describeProgress(view({ status: "queued", progress: 0, terminal: false })).indeterminate).toBe(true);
  });

  it("switches to a real percentage the moment progress advances above zero", () => {
    const d = describeProgress(view({ status: "running", progress: 0.4, terminal: false }));
    expect(d.indeterminate).toBe(false);
    expect(d.percent).toBe(40);
  });

  it("is never indeterminate once terminal — succeeded resolves to 100%", () => {
    const d = describeProgress(view({ status: "succeeded", progress: 1, terminal: true }));
    expect(d.indeterminate).toBe(false);
    expect(d.percent).toBe(100);
  });

  it("is not indeterminate on a terminal failure/cancel even at zero progress", () => {
    expect(describeProgress(view({ status: "failed", progress: 0, terminal: true })).indeterminate).toBe(false);
    expect(describeProgress(view({ status: "cancelled", progress: 0, terminal: true })).indeterminate).toBe(false);
  });
});
