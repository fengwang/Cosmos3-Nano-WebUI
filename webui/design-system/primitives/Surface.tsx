import type { ElementType, HTMLAttributes, ReactNode } from "react";

import styles from "./Surface.module.css";

export type SurfaceVariant = "raised" | "inset" | "flat";

export interface SurfaceProps extends HTMLAttributes<HTMLElement> {
  /** The semantic element to render (default `div`). */
  as?: ElementType;
  /** Neumorphic treatment. The shadow is decorative — never the sole affordance. */
  variant?: SurfaceVariant;
  children?: ReactNode;
}

/**
 * Token-driven neumorphic container. Pure render of props (server component, 0 JS).
 * `data-variant` exposes the treatment for tests/styling without leaking class names.
 */
export function Surface({
  as: Tag = "div",
  variant = "raised",
  className,
  children,
  ...rest
}: SurfaceProps) {
  const cls = [styles.surface, styles[variant], className].filter(Boolean).join(" ");
  return (
    <Tag className={cls} data-variant={variant} {...rest}>
      {children}
    </Tag>
  );
}
