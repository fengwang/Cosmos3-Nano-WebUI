// The 3D-vs-fallback decision (ACD: pure Calculation). Extracted from the workspace so the contract's
// headline safety property — a verified embodiment whose joint-map/URDF/width is wrong MUST refuse 3D and
// fall back to the 2D floor (INV-6/RK-12/RK-04) — is unit-testable, not buried in a component branch.

import type { ViewerMode } from "./embodiments";
import type { JointMapError } from "./jointmap";

export interface ViewerDecision {
  /** Render the 3D URDF view. */
  show3D: boolean;
  /** A non-null fallback reason to surface (why 3D is unavailable); null when 3D renders. */
  reason: string | null;
}

export interface ViewerInputs {
  domain: string;
  hasTrajectory: boolean;
  /** The width of the loaded trajectory data (0 when none). */
  trajectoryWidth: number;
  /** The embodiment's canonical action width (null if unknown). */
  canonicalWidth: number | null;
  mode: ViewerMode;
  hasMap: boolean;
  hasUrdf: boolean;
  /** A joint-map schema-validation error, if any (INV-6/RK-12). */
  configError: JointMapError | null;
  /** A runtime error reported by the WebGL seam (e.g. WebGL unavailable, URDF missing joints). */
  viewerError: string | null;
}

/**
 * Pure: decide whether to render the 3D view. 3D is shown ONLY for a verified-3D embodiment whose joint-map
 * validates, whose URDF exists, whose trajectory width matches the schema, and with no runtime viewer error.
 * Every other case falls back to the 2D plots with an explanatory reason (no misleading 3D motion).
 */
export function decideViewer(inputs: ViewerInputs): ViewerDecision {
  const { domain, hasTrajectory, trajectoryWidth, canonicalWidth, mode, hasMap, hasUrdf, configError, viewerError } = inputs;
  if (!hasTrajectory) return { show3D: false, reason: null };
  const label = domain || "This embodiment";
  if (mode === "fallback") {
    return { show3D: false, reason: `${label} is not a verified 3D embodiment; the 2D trajectory plots are the authoritative view.` };
  }
  if (!hasMap || !hasUrdf) {
    return { show3D: false, reason: `3D view unavailable: no joint-map or URDF for ${label}. Showing the 2D plots.` };
  }
  if (configError) {
    return { show3D: false, reason: `3D view unavailable: ${configError.message}. Showing the 2D plots.` };
  }
  if (canonicalWidth != null && trajectoryWidth > 0 && trajectoryWidth !== canonicalWidth) {
    return {
      show3D: false,
      reason: `Trajectory width ${trajectoryWidth} does not match the expected ${canonicalWidth} for ${label}; showing the 2D plots.`,
    };
  }
  if (viewerError) {
    return { show3D: false, reason: `3D view unavailable: ${viewerError}. Showing the 2D plots.` };
  }
  return { show3D: true, reason: null };
}
