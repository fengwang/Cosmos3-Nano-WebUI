import { statusLabel } from "@/lib/studio/format";

import styles from "./StatusBadge.module.css";

const GLYPH: Record<string, string> = {
  queued: "◌",
  running: "◐",
  succeeded: "✓",
  failed: "✕",
  cancelled: "⊘",
  submitting: "…",
};

/** Job status chip. Conveys state by text label + glyph + border-weight — never color alone (RK-18). */
export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={styles.badge} data-status={status}>
      <span aria-hidden="true" className={styles.glyph}>
        {GLYPH[status] ?? "•"}
      </span>
      <span>{statusLabel(status)}</span>
    </span>
  );
}
