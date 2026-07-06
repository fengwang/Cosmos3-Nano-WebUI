"use client";

import { useEffect, useState } from "react";

import { PillButton } from "@/design-system/components/PillButton";

type Theme = "light" | "hc";

/**
 * Toggles the high-contrast theme by setting `data-theme` on <html>. Initializes
 * from `prefers-contrast: more` on mount (progressive enhancement). State is conveyed
 * by the button label (text) + aria-pressed — never color alone.
 */
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  const apply = (next: Theme) => {
    document.documentElement.setAttribute("data-theme", next);
    setTheme(next);
  };

  useEffect(() => {
    if (window.matchMedia?.("(prefers-contrast: more)").matches) {
      apply("hc");
    }
  }, []);

  return (
    <PillButton selected={theme === "hc"} onClick={() => apply(theme === "hc" ? "light" : "hc")}>
      High contrast: {theme === "hc" ? "On" : "Off"}
    </PillButton>
  );
}
