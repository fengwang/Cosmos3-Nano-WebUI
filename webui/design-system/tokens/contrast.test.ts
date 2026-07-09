import { describe, expect, it } from "vitest";

import { contrastRatio, hexToRgb } from "@/lib/contrast";
import { AA_THRESHOLD, CONTRAST_PAIRS, THEMES } from "@/design-system/tokens/tokens";

// The contrast floor (NFR3 / RK-18): every audited foreground/background pair must
// meet WCAG 2.2 AA in BOTH themes. This is the deterministic form of the contract's
// "contrast ratios for text/interactive tokens meet AA (recorded)".
describe("token contrast audit — WCAG 2.2 AA floor", () => {
  for (const theme of THEMES) {
    const pairs = CONTRAST_PAIRS[theme];

    it(`${theme}: declares audited pairs`, () => {
      expect(pairs.length).toBeGreaterThan(0);
    });

    for (const p of pairs) {
      const min = AA_THRESHOLD[p.kind];
      it(`${theme}: "${p.name}" (${p.kind}) ${p.fg} on ${p.bg} ≥ ${min}:1`, () => {
        const ratio = contrastRatio(hexToRgb(p.fg), hexToRgb(p.bg));
        expect(ratio).toBeGreaterThanOrEqual(min);
      });
    }
  }

  it("guard: a deliberately sub-threshold pair fails the floor (non-vacuous)", () => {
    // Pale-on-pale: exactly the RK-18 trap. Proves the audit can fail.
    expect(contrastRatio(hexToRgb("#bbbbbb"), hexToRgb("#cccccc"))).toBeLessThan(3);
  });
});
