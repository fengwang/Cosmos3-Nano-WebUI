// Studio Data layer (ACD: inert, serializable values). No behavior, no I/O — only shape.
// The pure Calculations in this folder operate on these; the components/hooks are the Action shell.

import type { components } from "@/lib/api/schema";

/** The public generation modes the studio composes (the action UI + reasoning are separate). */
export type GenMode = "t2i" | "t2v" | "i2v" | "t2v_audio";

/** Conditioning media kinds the api recognizes (only `image` is browser-wirable for generation). */
export type MediaKind = "image" | "video" | "audio";

/** A file the user attached, already read into base64 (the Action that reads it lives in a hook). */
export interface AttachedMedia {
  kind: MediaKind;
  mime: string;
  name: string;
  bytes: number;
  dataBase64: string;
}

/** Generation params the presets/draft set; mapped to a GenerationBody by `request.ts`. */
export interface DraftParams {
  height?: number;
  width?: number;
  num_frames?: number;
  num_inference_steps?: number;
  seed?: number;
}

/** The in-progress compose request (edited in Compose, previewed in Inspect, run in Run). */
export interface Draft {
  mode: GenMode;
  prompt: string;
  negativePrompt?: string;
  preset: PresetId;
  params: DraftParams;
  media?: AttachedMedia;
}

/** Non-blocking-to-blocking advisories/flags surfaced to the user (severity drives ARIA role). */
export type Severity = "info" | "warn" | "error";
export interface Warning {
  severity: Severity;
  code: string;
  message: string;
}

/** A parameter preset id (catalog in `presets.ts`). */
export type PresetId = "standard-480" | "hi-720";

/** A persisted history record (localStorage; re-hydrated via GET /v1/jobs/{id}). */
export interface HistoryEntry {
  id: string;
  mode: string;
  summary: string;
  createdAt: string;
}

/** The wire generation body, straight from the frozen OpenAPI schema (single source of truth). */
export type GenerationBody = components["schemas"]["GenerationBody"];
export type Job = components["schemas"]["Job"];
export type JobStatus = components["schemas"]["JobStatus"];
