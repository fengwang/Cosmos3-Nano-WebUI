"use client";

import { useCallback } from "react";

/**
 * Announce async status through the app-shell polite live region (`#live-region` in the root layout).
 * The Action of touching the DOM is isolated here so callers just call `announce(text)` (NFR3 / EC-U4).
 */
export function useLiveRegion(): (message: string) => void {
  return useCallback((message: string) => {
    if (typeof document === "undefined") return;
    const region = document.getElementById("live-region");
    if (region) region.textContent = message;
  }, []);
}
