// Pure demo action-job body for the /action workspace (ACD Calculation; no React/DOM, host-testable).
// S6: the served checkpoint is implicit in the deployed stack — the workspace no longer selects it
// (FR-12); the body carries no `checkpoint` field. Refs: session_6/specs/webui-implicit-checkpoint.md.

import type { ActionBody } from "./useActionJob";

export const DEMO_CHUNK = 16;

/** The base demo ActionBody for an embodiment (mode-specific fields added by the caller). */
export function demoActionBody(domain: string): ActionBody {
  return {
    domain_name: domain,
    chunk_size: DEMO_CHUNK,
    seed: 123,
    resolution_tier: 480,
    view_point: "ego_view",
  };
}
