import { useEffect, useRef, useState } from "react";

/**
 * Elapsed-milliseconds ticker for a tracked job (ACD: an Action — wall-clock read + interval). Resets to
 * 0 when `key` changes (a new job) and stops ticking once `terminal`. Shared by both job trackers'
 * indeterminate state (RunPanel, ActionWorkspace). This is a plain elapsed readout — NOT progress: it is
 * never mapped to a percentage (R-08 forbids faking a percentage from elapsed time).
 */
export function useElapsed(key: string | undefined, terminal: boolean): number {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(0);

  useEffect(() => {
    startRef.current = Date.now();
    setElapsed(0);
  }, [key]);

  useEffect(() => {
    if (!key || terminal) return;
    const timer = setInterval(() => setElapsed(Date.now() - startRef.current), 500);
    return () => clearInterval(timer);
  }, [key, terminal]);

  return elapsed;
}
