import { describe, expect, it } from "vitest";

import { DEMO_CHUNK, demoActionBody } from "./demoBody";

describe("demoActionBody (action-viewer demo body)", () => {
  it("builds the base body shape the /v1/action route expects, with no checkpoint field (S6/FR-12)", () => {
    const body = demoActionBody("agibotworld", "policy");
    expect(body.domain_name).toBe("agibotworld");
    expect(body.resolution_tier).toBe(480);
    expect(body.view_point).toBe("ego_view");
    expect(body.seed).toBe(123);
    expect("checkpoint" in body).toBe(false);
  });

  it("attaches the shipped first-frame IMAGE for agibotworld policy (+ an instruction prompt)", () => {
    const body = demoActionBody("agibotworld", "policy");
    expect(body.image_path).toContain("/models/checkpoint/assets/");
    expect(body.image_path).toMatch(/example_action_fd_agibotworld_first_frame\.png$/);
    expect(body.video_path == null).toBe(true); // policy is image-conditioned, never a video
    expect((body.prompt ?? "").length).toBeGreaterThan(0);
    expect(body.chunk_size).toBe(DEMO_CHUNK);
  });

  it("attaches the shipped first-frame IMAGE for agibotworld forward_dynamics", () => {
    const body = demoActionBody("agibotworld", "forward_dynamics");
    expect(body.image_path).toMatch(/example_action_fd_agibotworld_first_frame\.png$/);
    expect(body.video_path == null).toBe(true);
  });

  it("sends a non-empty prompt for EVERY verified (embodiment, mode) — omni's video API requires it", () => {
    const cases: [string, string][] = [
      ["agibotworld", "policy"],
      ["agibotworld", "forward_dynamics"],
      ["av", "inverse_dynamics"],
    ];
    for (const [domain, mode] of cases) {
      const body = demoActionBody(domain, mode);
      expect((body.prompt ?? "").trim().length, `${domain}:${mode} must carry a prompt`).toBeGreaterThan(0);
    }
  });

  it("attaches the shipped av clip as VIDEO conditioning for inverse_dynamics (chunk matches the clip)", () => {
    const body = demoActionBody("av", "inverse_dynamics");
    expect(body.video_path).toContain("/models/checkpoint/assets/");
    expect(body.video_path).toMatch(/example_action_id_av_0_input\.mp4$/);
    expect(body.image_path == null).toBe(true); // inverse_dynamics is video-conditioned
    expect(body.chunk_size).toBe(60); // the shipped av clip is 61 frames → recover 60 transitions
  });

  it("returns the bare base body for an unknown (embodiment, mode) — no phantom conditioning", () => {
    const body = demoActionBody("unknown", "policy");
    expect(body.image_path == null).toBe(true);
    expect(body.video_path == null).toBe(true);
    expect(body.chunk_size).toBe(DEMO_CHUNK);
  });
});
