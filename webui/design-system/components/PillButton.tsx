"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

import styles from "./PillButton.module.css";

export type PillTone = "neutral" | "accent" | "danger";

export interface PillButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  tone?: PillTone;
  /** Toggle/selected state. Surfaced via aria-pressed + a border-weight delta (non-color). */
  selected?: boolean;
  children?: ReactNode;
}

/**
 * Pill-shaped button over a native <button> (free keyboard activation + disabled
 * semantics). Affordance carries a ≥3:1 border + a visible focus ring — never the
 * shadow alone (RK-18). `selected` adds aria-pressed and a border-weight signal.
 */
export function PillButton({
  tone = "neutral",
  selected,
  className,
  type,
  children,
  ...rest
}: PillButtonProps) {
  const cls = [
    styles.pill,
    styles[tone],
    selected ? styles.selected : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <button
      type={type ?? "button"}
      className={cls}
      data-tone={tone}
      data-selected={selected ? "true" : undefined}
      aria-pressed={selected === undefined ? undefined : selected}
      {...rest}
    >
      {children}
    </button>
  );
}
