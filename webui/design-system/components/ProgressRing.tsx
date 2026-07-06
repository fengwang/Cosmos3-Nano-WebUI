import styles from "./ProgressRing.module.css";

export interface ProgressRingProps {
  /** Progress 0–100 (clamped + rounded). Ignored when `indeterminate`. */
  value?: number;
  /** Accessible name + visible caption. */
  label: string;
  /**
   * When true, render an animated indeterminate arc — progress is unreadable (e.g. a sync mode that
   * emits no advancing progress). No numeric `%` and, per WAI-ARIA, no `aria-valuenow` (the standard
   * indeterminate signal); the accessible `aria-label` is kept.
   */
  indeterminate?: boolean;
  size?: number;
}

/**
 * Circular progress indicator. Determinate: value is conveyed by the progressbar role + aria-valuenow
 * AND a visible "N%" label — never by color alone. Indeterminate: an animated arc with no value (honors
 * `prefers-reduced-motion`). Pure render.
 */
export function ProgressRing({ value = 0, label, indeterminate = false, size = 96 }: ProgressRingProps) {
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  if (indeterminate) {
    return (
      <div className={styles.ring} role="progressbar" aria-label={label} style={{ width: size, height: size }}>
        <svg width={size} height={size} aria-hidden="true" className={styles.svg}>
          <circle className={styles.track} cx={center} cy={center} r={radius} strokeWidth={stroke} fill="none" />
          {/* A quarter-circumference arc; the CSS spins it about the ring centre → indeterminate motion. */}
          <circle
            className={styles.spinner}
            data-testid="ring-spinner"
            cx={center}
            cy={center}
            r={radius}
            strokeWidth={stroke}
            fill="none"
            strokeDasharray={`${circumference * 0.25} ${circumference * 0.75}`}
            strokeLinecap="round"
          />
        </svg>
      </div>
    );
  }

  const pct = Number.isFinite(value) ? Math.max(0, Math.min(100, Math.round(value))) : 0;
  const offset = circumference * (1 - pct / 100);

  return (
    <div
      className={styles.ring}
      role="progressbar"
      aria-label={label}
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} aria-hidden="true" className={styles.svg}>
        <circle
          className={styles.track}
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={stroke}
          fill="none"
        />
        <circle
          className={styles.value}
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${center} ${center})`}
        />
      </svg>
      <span className={styles.text} aria-hidden="true">
        {pct}%
      </span>
    </div>
  );
}
