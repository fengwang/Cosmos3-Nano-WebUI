// Pure demo action-job body for the /action workspace (ACD Calculation; no React/DOM, host-testable).
// S6: the served checkpoint is implicit in the deployed stack — the workspace no longer selects it
// (FR-12); the body carries no `checkpoint` field. Refs: session_6/specs/webui-implicit-checkpoint.md.
//
// AM-S3: "Run demo" now attaches the CHECKPOINT'S SHIPPED example conditioning per mode, so the button
// completes a real job instead of 422-ing (policy/forward_dynamics need an image; inverse_dynamics needs
// a video — the api rejects a job with no conditioning). The example assets are mounted read-only into
// the api container at /models/checkpoint/assets (deploy/docker-compose.*.yml), and the api trusts that
// dir via COSMOS3_INPUT_ALLOWLIST. Refs: docs/session_3 (R-12 UI-gap fix).

import type { ActionBody } from "./useActionJob";

export const DEMO_CHUNK = 16;

// In-container path of the checkpoint's shipped example inputs (mounted by the per-stack compose file).
const ASSETS = "/models/checkpoint/assets";

interface DemoConditioning {
  image_path?: string; // policy / forward_dynamics: a first-frame observation image
  video_path?: string; // inverse_dynamics: an input clip to recover actions from
  prompt?: string;
  chunk_size?: number; // override DEMO_CHUNK where a shipped clip has a fixed length
}

// The shipped demo input for each verified (embodiment, mode) — the v1-scope set (agibotworld
// policy/forward_dynamics; av inverse_dynamics). An entry's absence → the bare base body (no phantom
// conditioning), and the api still validates.
const DEMO_CONDITIONING: Record<string, DemoConditioning> = {
  "agibotworld:policy": {
    image_path: `${ASSETS}/example_action_fd_agibotworld_first_frame.png`,
    prompt: "Pickup items in the supermarket",
  },
  "agibotworld:forward_dynamics": {
    image_path: `${ASSETS}/example_action_fd_agibotworld_first_frame.png`,
    prompt: "Pickup items in the supermarket", // omni's video API requires a non-empty prompt for action
  },
  "av:inverse_dynamics": {
    video_path: `${ASSETS}/example_action_id_av_0_input.mp4`,
    chunk_size: 60, // the shipped av clip is 61 frames → recover 60 transitions (num_frames = chunk+1)
    prompt: "recover the action trajectory", // required by omni's video API; verified prompt (evidence/P1–P2)
  },
};

/** The demo ActionBody for an (embodiment, mode): the base + the shipped example conditioning that mode
 *  needs, so the "Run demo" button submits a complete, api-valid job. */
export function demoActionBody(domain: string, mode: string): ActionBody {
  const cond = DEMO_CONDITIONING[`${domain}:${mode}`] ?? {};
  const body: ActionBody = {
    domain_name: domain,
    chunk_size: cond.chunk_size ?? DEMO_CHUNK,
    seed: 123,
    resolution_tier: 480,
    view_point: "ego_view",
  };
  if (cond.image_path) body.image_path = cond.image_path;
  if (cond.video_path) body.video_path = cond.video_path;
  if (cond.prompt) body.prompt = cond.prompt;
  return body;
}
