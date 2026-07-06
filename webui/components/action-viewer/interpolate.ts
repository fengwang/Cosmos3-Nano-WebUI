// Interpolation (ACD: pure Calculations). Linear for scalar joints (revolute/continuous/prismatic);
// quaternion SLERP for orientation groups. SLERP is reserved for true multi-DoF orientations — a 1-DoF
// angle's "slerp" reduces to linear, so we lerp scalars and slerp only declared orientation quaternions.
// Defeats the "SLERP/linear mixed up → jittery/unnatural rotation" adversarial case. Refs: design D5.

export interface Quat {
  x: number;
  y: number;
  z: number;
  w: number;
}

/** Pure: linear interpolation; endpoints exact. */
export const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

/** Pure: normalize a quaternion (zero → identity-ish guard). */
export function normalizeQuat(q: Quat): Quat {
  const n = Math.hypot(q.x, q.y, q.z, q.w);
  if (n === 0) return { x: 0, y: 0, z: 0, w: 1 };
  return { x: q.x / n, y: q.y / n, z: q.z / n, w: q.w / n };
}

/** Pure: intrinsic XYZ Euler (radians) → quaternion (matches three.js `Euler` default order 'XYZ'). */
export function eulerToQuat(x: number, y: number, z: number): Quat {
  const cx = Math.cos(x / 2), sx = Math.sin(x / 2);
  const cy = Math.cos(y / 2), sy = Math.sin(y / 2);
  const cz = Math.cos(z / 2), sz = Math.sin(z / 2);
  return {
    x: sx * cy * cz + cx * sy * sz,
    y: cx * sy * cz - sx * cy * sz,
    z: cx * cy * sz + sx * sy * cz,
    w: cx * cy * cz - sx * sy * sz,
  };
}

/**
 * Pure: spherical linear interpolation between two orientations (normalized, shortest-arc). Falls back to
 * normalized-lerp when the quaternions are nearly parallel (numerically stable). The result is unit-norm.
 */
export function slerpQuat(a: Quat, b: Quat, t: number): Quat {
  const q0 = normalizeQuat(a);
  let q1 = normalizeQuat(b);
  let dot = q0.x * q1.x + q0.y * q1.y + q0.z * q1.z + q0.w * q1.w;
  // Shortest arc: if the dot is negative the quaternions are on opposite hemispheres; negate one.
  if (dot < 0) {
    q1 = { x: -q1.x, y: -q1.y, z: -q1.z, w: -q1.w };
    dot = -dot;
  }
  if (dot > 0.9995) {
    return normalizeQuat({
      x: lerp(q0.x, q1.x, t),
      y: lerp(q0.y, q1.y, t),
      z: lerp(q0.z, q1.z, t),
      w: lerp(q0.w, q1.w, t),
    });
  }
  const theta0 = Math.acos(dot);
  const theta = theta0 * t;
  const sinTheta0 = Math.sin(theta0);
  const s0 = Math.cos(theta) - (dot * Math.sin(theta)) / sinTheta0;
  const s1 = Math.sin(theta) / sinTheta0;
  return {
    x: s0 * q0.x + s1 * q1.x,
    y: s0 * q0.y + s1 * q1.y,
    z: s0 * q0.z + s1 * q1.z,
    w: s0 * q0.w + s1 * q1.w,
  };
}
