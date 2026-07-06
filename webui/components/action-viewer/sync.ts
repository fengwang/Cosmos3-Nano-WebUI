// Video-master timeline sync (ACD: pure Calculation). The trajectory JSON has NO fps and the rollout video
// is `chunk+1` frames, so sync is timeline-NORMALIZED, not fps-derived: the <video> element is the master
// clock (currentTime/duration ∈ [0,1]) and the trajectory is sampled across its full length. Refs: design D6.

export interface Sample {
  /** Lower bracketing frame index. */
  i0: number;
  /** Upper bracketing frame index (== i0 when the normalized position lands on a frame). */
  i1: number;
  /** Interpolation fraction in [0,1) between i0 and i1. */
  frac: number;
}

const clamp01 = (t: number): number => (t < 0 ? 0 : t > 1 ? 1 : t);

/**
 * Pure: map a normalized time `t ∈ [0,1]` onto a trajectory of `T` frames, returning the bracketing
 * indices + the interpolation fraction. Clamps out-of-range `t`; `T <= 1` collapses to frame 0.
 */
export function sampleIndex(normalizedT: number, T: number): Sample {
  if (T <= 1) return { i0: 0, i1: 0, frac: 0 };
  const t = clamp01(normalizedT);
  const f = t * (T - 1);
  const i0 = Math.floor(f);
  const i1 = Math.min(Math.ceil(f), T - 1);
  return { i0, i1, frac: f - i0 };
}

/** Pure: normalized time from a video clock (guards `duration` 0/NaN → 0). */
export function normalizedTime(currentTime: number, duration: number): number {
  if (!Number.isFinite(duration) || duration <= 0) return 0;
  return clamp01(currentTime / duration);
}

/** Pure: the nearest integer frame index for a normalized time (for the current-frame marker). */
export function currentFrame(normalizedT: number, T: number): number {
  if (T <= 1) return 0;
  return Math.round(clamp01(normalizedT) * (T - 1));
}
