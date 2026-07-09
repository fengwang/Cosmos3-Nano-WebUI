// Pure WCAG 2.x contrast Calculations — deterministic, no I/O (ACD: Calculations).
// Used by the token contrast audit to enforce the AA floor (NFR3 / RK-18).

export type Rgb = [number, number, number];

/** Parse a 6-digit hex color (leading '#' optional) into an [r,g,b] triple (0–255). */
export function hexToRgb(hex: string): Rgb {
  const n = hex.replace(/^#/, "");
  return [0, 2, 4].map((i) => parseInt(n.slice(i, i + 2), 16)) as Rgb;
}

/** sRGB 8-bit channel → linear-light component (WCAG transfer function). */
export function srgbChannelToLinear(channel: number): number {
  const c = channel / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

/** WCAG relative luminance of an sRGB color (0 = black, 1 = white). */
export function relLuminance([r, g, b]: Rgb): number {
  return (
    0.2126 * srgbChannelToLinear(r) +
    0.7152 * srgbChannelToLinear(g) +
    0.0722 * srgbChannelToLinear(b)
  );
}

/** WCAG contrast ratio in [1, 21], order-independent. */
export function contrastRatio(a: Rgb, b: Rgb): number {
  const la = relLuminance(a);
  const lb = relLuminance(b);
  const [hi, lo] = la >= lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}
