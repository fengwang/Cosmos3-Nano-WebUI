import { describe, expect, it } from "vitest";

import { compatibleModes, flagImpossible } from "@/lib/studio/modes";
import type { AttachedMedia, Draft } from "@/lib/studio/types";

const image: AttachedMedia = { kind: "image", mime: "image/png", name: "a.png", bytes: 10, dataBase64: "AA==" };
const video: AttachedMedia = { kind: "video", mime: "video/mp4", name: "a.mp4", bytes: 10, dataBase64: "AA==" };
const audio: AttachedMedia = { kind: "audio", mime: "audio/wav", name: "a.wav", bytes: 10, dataBase64: "AA==" };

function draft(over: Partial<Draft> = {}): Draft {
  return { mode: "t2v", prompt: "p", preset: "standard-480", params: {}, ...over };
}

describe("compatibleModes", () => {
  it("offers t2i/t2v/t2v_audio when no media is attached", () => {
    expect(compatibleModes(null)).toEqual(["t2i", "t2v", "t2v_audio"]);
  });

  it("adds i2v when an image is attached", () => {
    expect(compatibleModes("image/png")).toContain("i2v");
  });

  it("offers no generation mode for input video or audio", () => {
    expect(compatibleModes("video/mp4")).toEqual([]);
    expect(compatibleModes("audio/wav")).toEqual([]);
  });
});

describe("flagImpossible", () => {
  it("is empty with no media", () => {
    expect(flagImpossible(draft())).toEqual([]);
  });

  it("flags input video/audio as an error (no generation mode accepts them)", () => {
    expect(flagImpossible(draft({ media: video }))[0]).toMatchObject({ severity: "error", code: "input_media_unsupported" });
    expect(flagImpossible(draft({ media: audio }))[0]).toMatchObject({ severity: "error" });
  });

  it("info-flags an attached image when the mode is not i2v (it will be ignored)", () => {
    expect(flagImpossible(draft({ mode: "t2v", media: image }))[0]).toMatchObject({ severity: "info", code: "image_ignored" });
  });

  it("does not flag an image when the mode is i2v", () => {
    expect(flagImpossible(draft({ mode: "i2v", media: image }))).toEqual([]);
  });

  it("flags i2v with no image as a blocking error", () => {
    expect(flagImpossible(draft({ mode: "i2v" }))[0]).toMatchObject({ severity: "error", code: "i2v_needs_image" });
  });
});
