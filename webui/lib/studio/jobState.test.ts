import { describe, expect, it } from "vitest";

import { initialJobView, projectJob, reduceJobEvent } from "@/lib/studio/jobState";
import type { SseEvent } from "@/lib/sse/parseSse";

const ev = (event: string, data: Record<string, unknown> = {}): SseEvent => ({ event, data: JSON.stringify(data) });

describe("projectJob", () => {
  it("folds running → progress → succeeded into a terminal view with meta", () => {
    const view = projectJob([
      ev("running"),
      ev("progress", { progress: 0.5 }),
      ev("succeeded", { precision: "nvfp4", engine: "diffusers" }),
    ]);
    expect(view.status).toBe("succeeded");
    expect(view.progress).toBe(1);
    expect(view.terminal).toBe(true);
    expect(view.meta).toMatchObject({ precision: "nvfp4" });
  });

  it("clamps progress into [0,1]", () => {
    expect(reduceJobEvent(initialJobView(), ev("progress", { progress: 2 })).progress).toBe(1);
    expect(reduceJobEvent(initialJobView(), ev("progress", { progress: -1 })).progress).toBe(0);
  });

  it("surfaces a failed message", () => {
    const view = projectJob([ev("running"), ev("failed", { message: "OOM at decode" })]);
    expect(view.status).toBe("failed");
    expect(view.error?.message).toBe("OOM at decode");
    expect(view.terminal).toBe(true);
  });

  it("marks a cancelled job terminal", () => {
    expect(projectJob([ev("running"), ev("cancelled")]).status).toBe("cancelled");
  });

  it("appends a forward-compatible warning without terminating a running job", () => {
    const view = projectJob([ev("running"), ev("warning", { code: "preset_downgraded", message: "480→256" })]);
    expect(view.terminal).toBe(false);
    expect(view.warnings[0]).toMatchObject({ severity: "warn", code: "preset_downgraded" });
  });

  it("ignores heartbeats, unknown events, and malformed data", () => {
    const view = projectJob([ev("progress", { progress: 0.3 }), ev("heartbeat"), { event: "progress", data: "not-json" }, ev("mystery")]);
    expect(view.progress).toBe(0.3);
    expect(view.status).toBe("running");
  });
});
