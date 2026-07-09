"use client";

import { useId } from "react";
import type { TextareaHTMLAttributes } from "react";

import styles from "./Textarea.module.css";

export interface TextareaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "id"> {
  label: string;
  /** When set, marks the field aria-invalid and links a visible message (never color alone). */
  error?: string;
  id?: string;
}

/** Labelled multi-line input mirroring the design-system Input a11y (label assoc + error wiring). */
export function Textarea({ label, error, id, className, rows = 4, ...rest }: TextareaProps) {
  const reactId = useId();
  const fieldId = id ?? reactId;
  const errorId = `${fieldId}-error`;
  return (
    <div className={styles.field}>
      <label htmlFor={fieldId} className={styles.label}>
        {label}
      </label>
      <textarea
        id={fieldId}
        rows={rows}
        className={[styles.textarea, className].filter(Boolean).join(" ")}
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
