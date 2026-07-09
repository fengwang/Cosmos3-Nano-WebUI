// Client-side preset advisories (ACD: pure Calculation; RK-08). NON-BLOCKING by construction — these are
// `info`/`warn`, never `error`, so they never disable submission. They give the "downgraded preset"-class
// signal the api has no channel for yet (filed to S7); the api remains authoritative on hard limits (422).

import type { Draft, Warning } from "@/lib/studio/types";

/** Frame count above which the untiled-VAE decode peak becomes a notable VRAM/latency concern (RK-08). */
const LONG_FRAMES = 96;

/** Non-blocking advisories for a draft's preset/params (RK-08 high-res / long-frame envelope). */
export function advisoriesFor(draft: Draft): Warning[] {
  const out: Warning[] = [];
  const { height, num_frames } = draft.params;
  if (height != null && height >= 720) {
    out.push({
      severity: "warn",
      code: "hi_res_envelope",
      message:
        "720p uses the untiled-VAE decode peak — expect higher VRAM and latency. 720p is best-effort; 480 is the safe default.",
    });
  }
  if ((num_frames ?? 0) > LONG_FRAMES) {
    out.push({
      severity: "warn",
      code: "long_frames",
      message: `${num_frames} frames is a long rollout — generation may be slow and memory-heavy on a single GPU.`,
    });
  }
  return out;
}
