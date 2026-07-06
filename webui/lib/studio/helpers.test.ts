import { describe, expect, it } from "vitest";

import { formatElapsed, statusLabel } from "@/lib/studio/format";
import { artifactKindForMode, BYTE_CAPS, EXT_FOR_KIND, mediaKindFromMime, withinByteCap } from "@/lib/studio/media";
import { nextTabIndex } from "@/lib/studio/tabs";
import { downsamplePeaks } from "@/lib/studio/waveform";

describe("nextTabIndex", () => {
  it("wraps forward and backward", () => {
    expect(nextTabIndex(0, "ArrowRight", 4)).toBe(1);
    expect(nextTabIndex(3, "ArrowRight", 4)).toBe(0);
    expect(nextTabIndex(0, "ArrowLeft", 4)).toBe(3);
  });
  it("jumps with Home/End and ignores other keys", () => {
    expect(nextTabIndex(2, "Home", 4)).toBe(0);
    expect(nextTabIndex(1, "End", 4)).toBe(3);
    expect(nextTabIndex(2, "a", 4)).toBe(2);
  });
});

describe("formatElapsed", () => {
  it("formats M:SS and clamps negatives", () => {
    expect(formatElapsed(0)).toBe("0:00");
    expect(formatElapsed(65_000)).toBe("1:05");
    expect(formatElapsed(-5)).toBe("0:00");
  });
});

describe("statusLabel", () => {
  it("labels known statuses", () => {
    expect(statusLabel("running")).toBe("Running");
    expect(statusLabel("succeeded")).toBe("Done");
  });
});

describe("mediaKindFromMime / caps", () => {
  it("maps by MIME prefix", () => {
    expect(mediaKindFromMime("image/png")).toBe("image");
    expect(mediaKindFromMime("video/mp4")).toBe("video");
    expect(mediaKindFromMime("audio/wav")).toBe("audio");
    expect(mediaKindFromMime("application/json")).toBeNull();
    expect(mediaKindFromMime(null)).toBeNull();
  });
  it("enforces the byte cap", () => {
    expect(withinByteCap("image", BYTE_CAPS.image)).toBe(true);
    expect(withinByteCap("image", BYTE_CAPS.image + 1)).toBe(false);
  });
  it("maps a mode to its artifact kind + extension", () => {
    expect(artifactKindForMode("t2i")).toBe("image");
    expect(artifactKindForMode("t2v")).toBe("video");
    expect(artifactKindForMode("i2v")).toBe("video");
    expect(EXT_FOR_KIND.video).toBe("mp4");
  });
});

describe("downsamplePeaks", () => {
  it("returns the requested bucket count with peaks in [0,1]", () => {
    const peaks = downsamplePeaks(new Float32Array([0, 0.5, -1, 0.2, 0.9, -0.3, 0.1, 0.4]), 4);
    expect(peaks).toHaveLength(4);
    expect(Math.max(...peaks)).toBeLessThanOrEqual(1);
    expect(peaks[0]).toBeCloseTo(0.5);
    expect(peaks[1]).toBeCloseTo(1);
  });
  it("handles empty input and non-positive buckets", () => {
    expect(downsamplePeaks([], 4)).toEqual([]);
    expect(downsamplePeaks([0.1, 0.2], 0)).toEqual([]);
  });
});
