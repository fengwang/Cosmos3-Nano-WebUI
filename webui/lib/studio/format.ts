// Small display formatters (ACD: pure Calculations; run). DOM-free + unit-tested.

/** Elapsed milliseconds → "M:SS" (clamped at 0; minutes uncapped). */
export function formatElapsed(ms: number): string {
  const totalSec = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/** A short human label for a job status (the StatusBadge text — never color alone). */
export function statusLabel(status: string): string {
  return (
    { queued: "Queued", running: "Running", succeeded: "Done", failed: "Failed", cancelled: "Cancelled", submitting: "Submitting" } as Record<string, string>
  )[status] ?? status;
}
