// Verified-embodiment registry + 3D-vs-fallback routing (ACD: inert Data + pure Calculations; no I/O).
// Canonical action widths MIRROR `api/preprocessing/action_schema.py` (`_RAW_ACTION_DIM`); drift here is a
// bug the joint-map validation + the report's guard note defend against (RK-12). Only the S4-verified set
// (`agibotworld` FD/policy 29-D; `av` ID 9-D) appears — the contract forbids new embodiments.

/** Canonical (unpadded) per-embodiment action width — mirrors the engine table (S4). */
export const CANONICAL_WIDTH: Record<string, number> = {
  agibotworld: 29,
  av: 9,
};

/** The single embodiment given the 3D/URDF path (articulated humanoid). Everything else is 2D-only. */
const VERIFIED_3D = new Set<string>(["agibotworld"]);

export type ViewerMode = "3d" | "fallback";

/** Pure: which viewer path an embodiment gets. A non-verified domain (incl. the `av` vehicle, which is not
 *  a joint tree) is always the 2D-plot fallback — never a misleading 3D robot. */
export function viewerModeFor(domain: string): ViewerMode {
  return VERIFIED_3D.has(domain) ? "3d" : "fallback";
}

/** Pure: the canonical action width for a domain, or `null` if unknown. */
export function canonicalWidthOf(domain: string): number | null {
  return domain in CANONICAL_WIDTH ? CANONICAL_WIDTH[domain] : null;
}

/** The embodiments the viewer offers (the S4-verified set only). */
export const VERIFIED_EMBODIMENTS: readonly string[] = ["agibotworld", "av"] as const;
