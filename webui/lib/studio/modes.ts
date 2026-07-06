// MIME → compatible generation modes + impossible-combo flagging (ACD: pure Calculations; F3).
// The api accepts conditioning media only as an inline image (i2v) or a trusted path; input video/audio
// is consumed by NO generation mode (reasoning takes media only via a trusted path — not browser-wirable).
// These functions are the edge guard behind Compose's "propose compatible modes / flag impossible combos".

import type { Draft, GenMode, Warning } from "@/lib/studio/types";

const BASE_MODES: GenMode[] = ["t2i", "t2v", "t2v_audio"];

/** The generation modes compatible with the attached media's MIME (null = no media). */
export function compatibleModes(mime: string | null): GenMode[] {
  if (!mime) return [...BASE_MODES];
  if (mime.startsWith("image/")) return ["t2i", "t2v", "i2v", "t2v_audio"];
  return []; // input video/audio: no generation mode consumes them
}

/**
 * Flags for the current draft's mode/media combination:
 *  - input video/audio attached  → blocking `error` (no generation mode accepts it);
 *  - image attached but mode ≠ i2v → non-blocking `info` (the image is ignored for that mode);
 *  - otherwise → no flags.
 */
export function flagImpossible(draft: Draft): Warning[] {
  const media = draft.media;
  // Non-image input is accepted by no generation mode at all (blocking).
  if (media && media.kind !== "image") {
    return [
      {
        severity: "error",
        code: "input_media_unsupported",
        message: `Input ${media.kind} is not accepted by any generation mode (image conditioning only). Remove it or switch to a text-driven mode.`,
      },
    ];
  }
  // i2v requires a conditioning image (blocking).
  if (draft.mode === "i2v" && !media) {
    return [
      {
        severity: "error",
        code: "i2v_needs_image",
        message: "Image → Video (i2v) needs a conditioning image. Attach one or pick a text-driven mode.",
      },
    ];
  }
  // An attached image on a non-i2v mode is simply ignored (non-blocking).
  if (media && draft.mode !== "i2v") {
    return [
      {
        severity: "info",
        code: "image_ignored",
        message: `The attached image is only used by Image → Video (i2v); it is ignored for ${draft.mode}.`,
      },
    ];
  }
  return [];
}

/** Convenience: a blocking flag means submission must be disabled. */
export function hasBlockingFlag(flags: Warning[]): boolean {
  return flags.some((f) => f.severity === "error");
}
