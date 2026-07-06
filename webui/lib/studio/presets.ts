// Parameter presets (ACD: inert catalog + pure mappers; F3 Inspect).
// Bounds mirror api/preprocessing/limits.py (resolutions {256,480,720}; num_frames ≤ 720) to reduce
// avoidable 422 round-trips — the SERVER stays authoritative (a breach still 422s, surfaced friendly).

import type { Draft, DraftParams, PresetId } from "@/lib/studio/types";

export interface Preset {
  id: PresetId;
  label: string;
  description: string;
  params: DraftParams;
}

/** The preset catalog. */
export const PRESETS: Record<PresetId, Preset> = {
  "standard-480": {
    id: "standard-480",
    label: "Standard · 480p",
    description: "Balanced default (640×480, 4:3).",
    params: { height: 480, width: 640, num_frames: 33, num_inference_steps: 30 },
  },
  "hi-720": {
    id: "hi-720",
    label: "High · 720p",
    description: "Best-effort high resolution (1280×720, 16:9; higher VRAM/latency — see advisory).",
    params: { height: 720, width: 1280, num_frames: 49, num_inference_steps: 35 },
  },
};

export const PRESET_LIST: Preset[] = [PRESETS["standard-480"], PRESETS["hi-720"]];

/** Pure: the params for a preset (a fresh copy — never the shared catalog object). */
export function presetParams(id: PresetId): DraftParams {
  return { ...PRESETS[id].params };
}

/** Pure: a new draft with the preset applied (id + params). Input draft is unchanged. */
export function applyPreset(draft: Draft, id: PresetId): Draft {
  return { ...draft, preset: id, params: presetParams(id) };
}
