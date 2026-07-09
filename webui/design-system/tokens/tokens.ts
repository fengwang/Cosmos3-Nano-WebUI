// Single source of truth for design tokens (ACD: Data) + a pure CSS emitter
// (Calculation). The root layout injects `themesCss()` so the audited hex values
// here ARE the runtime CSS variable values — no .css/.ts drift is possible.
//
// Two layers (RK-18 / NFR3):
//   - decorative: --shadow-light/--shadow-dark, surface tints (the neumorphic feel)
//   - contrast-bearing: --text*, --line, --focus, --accent (never below WCAG AA)
// State is never signalled by shadow/color alone (see components + non-color rule).

export type ThemeName = "light" | "hc";
export const THEMES: readonly ThemeName[] = ["light", "hc"] as const;

export type PairKind = "text-normal" | "text-large" | "non-text";

/** WCAG 2.2 minima: 1.4.3 (text) and 1.4.11 (non-text/UI). */
export const AA_THRESHOLD: Record<PairKind, number> = {
  "text-normal": 4.5,
  "text-large": 3,
  "non-text": 3,
};

/** Per-theme color tokens. Contrast-audited values live here. */
export const COLOR_TOKENS: Record<ThemeName, Record<string, string>> = {
  light: {
    "--surface": "#e6eaf0",
    "--surface-sunken": "#dfe4ec",
    "--shadow-light": "#ffffff",
    "--shadow-dark": "#c3cbd9",
    "--text": "#1e2632",
    "--text-muted": "#46505f",
    "--accent": "#15795a",
    "--on-accent": "#ffffff",
    "--line": "#6f7a8a",
    "--focus": "#1560c4",
    "--danger": "#c0392b",
    "--danger-text": "#a52f23",
    "--scrim": "rgba(20, 26, 36, 0.45)",
  },
  hc: {
    "--surface": "#ffffff",
    "--surface-sunken": "#eef1f6",
    "--shadow-light": "#ffffff",
    "--shadow-dark": "#b9c1cf",
    "--text": "#000000",
    "--text-muted": "#1f2733",
    "--accent": "#0b5c43",
    "--on-accent": "#ffffff",
    "--line": "#1a2330",
    "--focus": "#08306b",
    "--danger": "#8a1a10",
    "--danger-text": "#7a1109",
    "--scrim": "rgba(0, 0, 0, 0.6)",
  },
};

/** Theme-independent scale tokens (radii, spacing, the dual-shadow recipe, motion). */
export const SCALE_TOKENS: Record<string, string> = {
  "--radius-sm": "8px",
  "--radius-md": "14px",
  "--radius-lg": "22px",
  "--radius-pill": "999px",
  "--space-1": "4px",
  "--space-2": "8px",
  "--space-3": "12px",
  "--space-4": "16px",
  "--space-5": "24px",
  "--space-6": "32px",
  "--shadow-raised":
    "6px 6px 14px var(--shadow-dark), -6px -6px 14px var(--shadow-light)",
  "--shadow-raised-sm":
    "3px 3px 8px var(--shadow-dark), -3px -3px 8px var(--shadow-light)",
  "--shadow-inset":
    "inset 4px 4px 10px var(--shadow-dark), inset -4px -4px 10px var(--shadow-light)",
  "--focus-ring-width": "3px",
  "--motion-fast": "140ms",
  "--motion-base": "220ms",
  "--ease": "cubic-bezier(0.22, 1, 0.36, 1)",
};

export interface ContrastPair {
  name: string;
  fg: string; // resolved hex
  bg: string; // resolved hex
  kind: PairKind;
}

interface PairSpec {
  name: string;
  fg: string; // token name
  bg: string; // token name
  kind: PairKind;
}

// The foreground/background relationships the UI actually relies on.
const PAIR_SPECS: readonly PairSpec[] = [
  { name: "body text on surface", fg: "--text", bg: "--surface", kind: "text-normal" },
  { name: "muted text on surface", fg: "--text-muted", bg: "--surface", kind: "text-normal" },
  { name: "muted/placeholder text on sunken", fg: "--text-muted", bg: "--surface-sunken", kind: "text-normal" },
  { name: "body text on sunken", fg: "--text", bg: "--surface-sunken", kind: "text-normal" },
  { name: "label on accent", fg: "--on-accent", bg: "--accent", kind: "text-normal" },
  { name: "interactive border on surface", fg: "--line", bg: "--surface", kind: "non-text" },
  { name: "focus ring on surface", fg: "--focus", bg: "--surface", kind: "non-text" },
  { name: "accent indicator on surface", fg: "--accent", bg: "--surface", kind: "non-text" },
  { name: "error text on surface", fg: "--danger-text", bg: "--surface", kind: "text-normal" },
  { name: "error border on surface", fg: "--danger", bg: "--surface", kind: "non-text" },
];

const resolvePairs = (theme: ThemeName): ContrastPair[] =>
  PAIR_SPECS.map((s) => ({
    name: s.name,
    fg: COLOR_TOKENS[theme][s.fg],
    bg: COLOR_TOKENS[theme][s.bg],
    kind: s.kind,
  }));

export const CONTRAST_PAIRS: Record<ThemeName, ContrastPair[]> = {
  light: resolvePairs("light"),
  hc: resolvePairs("hc"),
};

const declare = (vars: Record<string, string>): string =>
  Object.entries(vars)
    .map(([k, v]) => `${k}:${v}`)
    .join(";");

/**
 * Render the token layer as CSS text for `<style>` injection by the root layout.
 * `:root` carries the light theme + scale; `[data-theme="hc"]` overrides colors.
 * Pure (Calculation) — same tokens in, same string out.
 */
export function themesCss(): string {
  return [
    `:root{${declare(COLOR_TOKENS.light)};${declare(SCALE_TOKENS)}}`,
    `:root[data-theme="hc"]{${declare(COLOR_TOKENS.hc)}}`,
  ].join("\n");
}
