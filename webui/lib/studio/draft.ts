// The draft reducer (ACD: pure state transition; studio-shell). No I/O — the Context provider in the
// (studio) layout is the only place this is wired to React. Switching to a mode that cannot use the
// attached media as conditioning drops the media (only an image+i2v pairing is usable).

import { applyPreset } from "@/lib/studio/presets";
import type { AttachedMedia, Draft, DraftParams, GenMode, PresetId } from "@/lib/studio/types";

export type DraftAction =
  | { type: "setMode"; mode: GenMode }
  | { type: "setPrompt"; value: string }
  | { type: "setNegative"; value: string }
  | { type: "applyPreset"; id: PresetId }
  | { type: "setParam"; key: keyof DraftParams; value: number | undefined }
  | { type: "attachMedia"; media: AttachedMedia }
  | { type: "clearMedia" }
  | { type: "reset" };

const DEFAULT_PRESET: PresetId = "hi-720";

/** A fresh default draft (t2v, the hi-720 720p preset — UX-S2: 720p is the default for video, agreeing
 * with the server's mode-aware default). standard-480 stays available. S6: the served checkpoint is
 * implicit in the deployed stack — the WebUI no longer selects it (FR-12). */
export function initialDraft(): Draft {
  return applyPreset({ mode: "t2v", prompt: "", preset: DEFAULT_PRESET, params: {} }, DEFAULT_PRESET);
}

/** Is the attached media usable as conditioning for `mode`? Only an image feeds i2v. */
function mediaUsableBy(media: AttachedMedia | undefined, mode: GenMode): boolean {
  return media?.kind === "image" && mode === "i2v";
}

export function draft(state: Draft, action: DraftAction): Draft {
  switch (action.type) {
    case "setMode":
      return { ...state, mode: action.mode, media: mediaUsableBy(state.media, action.mode) ? state.media : undefined };
    case "setPrompt":
      return { ...state, prompt: action.value };
    case "setNegative":
      return { ...state, negativePrompt: action.value || undefined };
    case "applyPreset":
      return applyPreset(state, action.id);
    case "setParam": {
      const params = { ...state.params, [action.key]: action.value };
      if (action.value === undefined) delete params[action.key];
      return { ...state, params };
    }
    case "attachMedia":
      return { ...state, media: action.media };
    case "clearMedia":
      return { ...state, media: undefined };
    case "reset":
      return initialDraft();
    default:
      return state;
  }
}
