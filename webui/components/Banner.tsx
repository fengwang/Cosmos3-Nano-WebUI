import type { ReactNode } from "react";

import type { Severity, Warning } from "@/lib/studio/types";

import styles from "./Banner.module.css";

/** error → assertive `alert`; warn/info → polite `status`. */
const ROLE: Record<Severity, "alert" | "status"> = { error: "alert", warn: "status", info: "status" };
const GLYPH: Record<Severity, string> = { error: "⚠", warn: "⚠", info: "ℹ" };

export function Banner({ severity, children }: { severity: Severity; children: ReactNode }) {
  return (
    <div className={styles.banner} data-severity={severity} role={ROLE[severity]}>
      <span aria-hidden="true" className={styles.glyph}>
        {GLYPH[severity]}
      </span>
      <div className={styles.body}>{children}</div>
    </div>
  );
}

/** Render a list of warnings/advisories/errors as banners (empty → nothing). */
export function WarningList({ warnings }: { warnings: Warning[] }) {
  if (warnings.length === 0) return null;
  return (
    <ul className={styles.list}>
      {warnings.map((w, i) => (
        <li key={`${w.code}-${i}`}>
          <Banner severity={w.severity}>{w.message}</Banner>
        </li>
      ))}
    </ul>
  );
}
