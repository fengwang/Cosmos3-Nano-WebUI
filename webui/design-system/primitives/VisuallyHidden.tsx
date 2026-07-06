import type { ReactNode } from "react";

import styles from "./VisuallyHidden.module.css";

/** Renders text for assistive tech only — present in the a11y tree, off-screen visually. */
export function VisuallyHidden({ children }: { children: ReactNode }) {
  return <span className={styles.visuallyHidden}>{children}</span>;
}
