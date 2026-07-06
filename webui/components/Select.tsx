"use client";

import { useId } from "react";
import type { SelectHTMLAttributes } from "react";

import styles from "./Select.module.css";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "id"> {
  label: string;
  options: SelectOption[];
  id?: string;
}

/** Labelled native <select> (free keyboard + a11y); programmatically associated label. */
export function Select({ label, options, id, className, ...rest }: SelectProps) {
  const reactId = useId();
  const selectId = id ?? reactId;
  return (
    <div className={styles.field}>
      <label htmlFor={selectId} className={styles.label}>
        {label}
      </label>
      <select id={selectId} className={[styles.select, className].filter(Boolean).join(" ")} {...rest}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
