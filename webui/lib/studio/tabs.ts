// Roving-focus index math for the Tabs primitive (ACD: pure Calculation; studio-shell). Extracted so the
// keyboard logic is unit-tested without a DOM; Tabs.tsx is a thin wrapper that applies the result.

/** The next focused tab index for a roving-tablist key press (wraps; Home/End jump). */
export function nextTabIndex(current: number, key: string, count: number): number {
  if (count <= 0) return 0;
  switch (key) {
    case "ArrowRight":
    case "ArrowDown":
      return (current + 1) % count;
    case "ArrowLeft":
    case "ArrowUp":
      return (current - 1 + count) % count;
    case "Home":
      return 0;
    case "End":
      return count - 1;
    default:
      return current;
  }
}
