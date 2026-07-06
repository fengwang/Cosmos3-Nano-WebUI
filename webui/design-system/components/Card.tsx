import type { ReactNode } from "react";

import { Surface } from "../primitives/Surface";

import styles from "./Card.module.css";

export interface CardProps {
  /** When set, the card becomes a labelled `region` landmark with a heading. */
  title?: string;
  children?: ReactNode;
  className?: string;
}

/**
 * Extruded neumorphic card. With a title it renders a labelled region + heading for
 * screen-reader navigation; without one it is a plain raised surface. Pure render.
 */
export function Card({ title, children, className }: CardProps) {
  const cls = [styles.card, className].filter(Boolean).join(" ");
  if (title) {
    return (
      <Surface as="section" variant="raised" className={cls} aria-label={title}>
        <h3 className={styles.title}>{title}</h3>
        <div className={styles.body}>{children}</div>
      </Surface>
    );
  }
  return (
    <Surface variant="raised" className={cls}>
      {children}
    </Surface>
  );
}
