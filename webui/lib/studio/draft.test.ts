import { describe, expect, it } from "vitest";

import { draft, initialDraft } from "@/lib/studio/draft";
import type { AttachedMedia, Draft } from "@/lib/studio/types";

const image: AttachedMedia = { kind: "image", mime: "image/png", name: "a.png", bytes: 10, dataBase64: "QQ==" };

describe("initialDraft", () => {
  it("defaults to t2v with the standard-480 preset applied", () => {
    const d = initialDraft();
    expect(d.mode).toBe("t2v");
    expect(d.preset).toBe("standard-480");
    expect(d.params.height).toBe(480);
    expect(d.params.width).toBe(640);
  });

  it("carries no checkpoint field (S6/FR-12: the deployed stack's checkpoint is implicit)", () => {
    expect("checkpoint" in initialDraft()).toBe(false);
  });
});

describe("draft reducer", () => {
  it("is pure (does not mutate the input state)", () => {
    const d = initialDraft();
    draft(d, { type: "setPrompt", value: "hello" });
    expect(d.prompt).toBe("");
  });

  it("setPrompt updates the prompt", () => {
    expect(draft(initialDraft(), { type: "setPrompt", value: "hi" }).prompt).toBe("hi");
  });

  it("keeps an attached image when switching to i2v", () => {
    const withImage: Draft = { ...initialDraft(), media: image };
    expect(draft(withImage, { type: "setMode", mode: "i2v" }).media).toEqual(image);
  });

  it("drops the conditioning image when leaving i2v for t2i", () => {
    const i2v: Draft = { ...initialDraft(), mode: "i2v", media: image };
    expect(draft(i2v, { type: "setMode", mode: "t2i" }).media).toBeUndefined();
  });

  it("applyPreset swaps the params deterministically", () => {
    expect(draft(initialDraft(), { type: "applyPreset", id: "hi-720" }).params.height).toBe(720);
  });

  it("setParam updates a single field", () => {
    const d = draft(initialDraft(), { type: "setParam", key: "seed", value: 42 });
    expect(d.params.seed).toBe(42);
    expect(d.params.height).toBe(480);
  });

  it("setParam with undefined clears the field", () => {
    const withSeed = draft(initialDraft(), { type: "setParam", key: "seed", value: 42 });
    const cleared = draft(withSeed, { type: "setParam", key: "seed", value: undefined });
    expect(cleared.params.seed).toBeUndefined();
  });

  it("applyPreset clears manual seed override", () => {
    const withSeed = draft(initialDraft(), { type: "setParam", key: "seed", value: 42 });
    const after = draft(withSeed, { type: "applyPreset", id: "hi-720" });
    expect(after.params.seed).toBeUndefined();
    expect(after.params.height).toBe(720);
    expect(after.params.width).toBe(1280);
  });
});
