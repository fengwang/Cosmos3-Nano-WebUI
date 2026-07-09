import { describe, expect, it } from "vitest";

import { buildRequest } from "@/lib/studio/request";
import type { AttachedMedia, Draft } from "@/lib/studio/types";

const image: AttachedMedia = { kind: "image", mime: "image/png", name: "a.png", bytes: 10, dataBase64: "QUJD" };

function draft(over: Partial<Draft> = {}): Draft {
  return { mode: "t2v", prompt: "a robot wiping a plate", preset: "standard-480", params: { height: 480, width: 640, num_frames: 33, num_inference_steps: 30 }, ...over };
}

describe("buildRequest", () => {
  it("routes each mode to its typed endpoint", () => {
    expect(buildRequest(draft({ mode: "t2i" })).path).toBe("/v1/generation/t2i");
    expect(buildRequest(draft({ mode: "t2v" })).path).toBe("/v1/generation/t2v");
    expect(buildRequest(draft({ mode: "i2v", media: image })).path).toBe("/v1/generation/i2v");
    expect(buildRequest(draft({ mode: "t2v_audio" })).path).toBe("/v1/generation/t2v_audio");
  });

  it("carries the prompt, seed and present params, with no checkpoint field (S6/FR-12)", () => {
    const { body } = buildRequest(draft({ negativePrompt: "blurry" }));
    expect(body.prompt).toBe("a robot wiping a plate");
    expect("checkpoint" in body).toBe(false);
    expect(body.seed).toBe(123);
    expect(body.height).toBe(480);
    expect(body.width).toBe(640);
    expect(body.num_frames).toBe(33);
    expect(body.negative_prompt).toBe("blurry");
  });

  it("omits num_frames for t2i (server forces a single frame)", () => {
    expect(buildRequest(draft({ mode: "t2i" })).body.num_frames).toBeUndefined();
  });

  it("includes the inline image only for i2v", () => {
    expect(buildRequest(draft({ mode: "i2v", media: image })).body.image).toEqual({ kind: "image", data_base64: "QUJD" });
    expect(buildRequest(draft({ mode: "t2v", media: image })).body.image).toBeUndefined();
  });

  it("omits absent optional fields (no nulls)", () => {
    const { body } = buildRequest(draft({ negativePrompt: undefined, params: {} }));
    expect("negative_prompt" in body).toBe(false);
    expect("height" in body).toBe(false);
    expect("width" in body).toBe(false);
    expect("resolution" in body).toBe(false);
  });

  it("does not send resolution field", () => {
    const { body } = buildRequest(draft());
    expect("resolution" in body).toBe(false);
  });

  it("uses custom seed from params", () => {
    const { body } = buildRequest(draft({ params: { ...draft().params, seed: 42 } }));
    expect(body.seed).toBe(42);
  });

  it("defaults seed to 123 when absent", () => {
    const { body } = buildRequest(draft({ params: { height: 720, width: 1280 } }));
    expect(body.seed).toBe(123);
  });
});
