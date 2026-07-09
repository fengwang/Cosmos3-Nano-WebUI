// Representative trajectory fixture (ACD: pure Calculation). Used to drive a forward-dynamics demo (the
// actions ARE the FD input) and the human-visual-gate sweep — a known, smooth motion that exercises every
// mapped dimension through a visible range so an axis-swap/scale bug is apparent. Deterministic.

import { eulerToQuat } from "./interpolate";

/**
 * Pure: a `[T][width]` demo trajectory. Scalar dims oscillate (phase-shifted per dim, so each joint moves
 * distinctly); an optional `quatDims` 4-tuple is filled with a chest quaternion rotating about Z across the
 * rollout (so the SLERP orientation path is exercised). Amplitude is modest to stay within typical limits.
 */
export function demoTrajectory(width: number, T: number, quatDims?: [number, number, number, number]): number[][] {
  const frames: number[][] = [];
  for (let t = 0; t < T; t++) {
    const p = T > 1 ? t / (T - 1) : 0;
    const row = Array.from({ length: width }, (_, d) => Math.sin(p * Math.PI * 2 + d * 0.5) * 0.6);
    if (quatDims) {
      const q = eulerToQuat(0, 0, p * Math.PI); // rotate the chest about Z over the rollout
      const [ix, iy, iz, iw] = quatDims;
      row[ix] = q.x;
      row[iy] = q.y;
      row[iz] = q.z;
      row[iw] = q.w;
    }
    frames.push(row);
  }
  return frames;
}
