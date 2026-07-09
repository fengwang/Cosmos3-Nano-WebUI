"use client";

import { useId } from "react";
import type { InputHTMLAttributes } from "react";

import styles from "./Input.module.css";

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "id"> {
  label: string;
  /** When set, the input is marked aria-invalid and linked to a visible message. */
  error?: string;
  id?: string;
}

/**
 * Labelled text input. The label is programmatically associated; an error is conveyed
 * by text + an icon glyph + aria-invalid/aria-describedby — never by color alone (1.4.1).
 */
export function Input({ label, error, id, className, ...rest }: InputProps) {
  const reactId = useId();
  const inputId = id ?? reactId;
  const errorId = `${inputId}-error`;
  return (
    <div className={styles.field}>
      <label htmlFor={inputId} className={styles.label}>
        {label}
      </label>
      <input
        id={inputId}
        className={[styles.input, className].filter(Boolean).join(" ")}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...rest}
      />
      {error ? (
        <p id={errorId} className={styles.error} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
