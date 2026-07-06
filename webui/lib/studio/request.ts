// Draft → typed generation request (ACD: pure Calculation; F3/D8). Maps the studio Draft to the frozen
// {path, GenerationBody} the BFF proxy forwards. Inline image conditioning rides as InlineMedia base64
// (the only browser-wirable conditioning path; multipart-to-api is an api/S12 concern).

import type { ApiPath } from "@/lib/api/client";
import type { Draft, GenerationBody, GenMode } from "@/lib/studio/types";

const PATH: Record<GenMode, ApiPath> = {
  t2i: "/v1/generation/t2i",
  t2v: "/v1/generation/t2v",
  i2v: "/v1/generation/i2v",
  t2v_audio: "/v1/generation/t2v_audio",
};

/** The generation endpoint + JSON body for a draft. Absent optional fields are omitted (not nulled).
 * S6: no `checkpoint` field — the deployed stack serves its single checkpoint implicitly (FR-12). */
export function buildRequest(draft: Draft): { path: ApiPath; body: GenerationBody } {
  const body: GenerationBody = { prompt: draft.prompt, seed: draft.params.seed ?? 123 };
  if (draft.negativePrompt) body.negative_prompt = draft.negativePrompt;
  const { height, width, num_frames, num_inference_steps } = draft.params;
  if (height != null) body.height = height;
  if (width != null) body.width = width;
  if (num_inference_steps != null) body.num_inference_steps = num_inference_steps;
  if (draft.mode !== "t2i" && num_frames != null) body.num_frames = num_frames;
  // Inline conditioning image only applies to i2v (the other modes ignore an attached image).
  if (draft.mode === "i2v" && draft.media?.kind === "image") {
    body.image = { kind: "image", data_base64: draft.media.dataBase64 };
  }
  return { path: PATH[draft.mode], body };
}

/** The api mode label for the chosen draft (matches the Job.mode the server reports). */
export function modeLabel(mode: GenMode): string {
  return { t2i: "Text → Image", t2v: "Text → Video", i2v: "Image → Video", t2v_audio: "Text → Video + Audio" }[mode];
}
