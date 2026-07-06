"use client";

import { useMemo } from "react";

import { Banner } from "@/components/Banner";

import { dimSeries, plotPath, toPolylinePoints } from "./plot";
import styles from "./TrajectoryPlots.module.css";

const PLOT_W = 160;
const PLOT_H = 44;

export interface TrajectoryPlotsProps {
  /** [T][width] trajectory. */
  frames: number[][];
  width: number;
  /** Per-dim visibility (index = dim); absent → visible. */
  visibleDims: boolean[];
  /** Current frame index (the shared timeline marker). */
  currentFrame: number;
  /** Optional per-dim labels (joint names for a mapped embodiment). */
  labels?: string[];
  /** When set, a non-color-only banner explaining why the 3D view is unavailable (the fallback reason). */
  reason?: string | null;
}

/**
 * The GUARANTEED FLOOR: per-dimension polyline plots of the raw trajectory. Makes no semantic claim about
 * the dims, so it is correct for any embodiment — the only view for `av`/unverified, and shown alongside
 * the 3D view for `agibotworld`. A `reason` renders a fallback banner (defeats the "no fallback" case).
 */
export function TrajectoryPlots({ frames, width, visibleDims, currentFrame, labels, reason }: TrajectoryPlotsProps) {
  const T = frames.length;
  const markerX = T > 1 ? (Math.min(Math.max(currentFrame, 0), T - 1) / (T - 1)) * PLOT_W : 0;

  // The per-dim polyline geometry depends only on the data/visibility, NOT the timeline — memoize it so
  // scrubbing/playback (which only moves the marker + the value readout) doesn't recompute 29×O(T) SVGs.
  const cells = useMemo(
    () =>
      Array.from({ length: width }, (_, d) => d)
        .filter((d) => visibleDims[d] !== false)
        .map((d) => {
          const series = dimSeries(frames, d);
          return { d, series, points: toPolylinePoints(plotPath(series, PLOT_W, PLOT_H)), label: labels?.[d] ?? `dim ${d}` };
        }),
    [frames, width, visibleDims, labels],
  );

  return (
    <div className={styles.plots} data-testid="trajectory-plots">
      {reason ? <Banner severity="warn">{reason}</Banner> : null}
      <ul className={styles.grid}>
        {cells.map(({ d, series, points, label }) => {
          const value = series[Math.min(Math.max(currentFrame, 0), series.length - 1)] ?? 0;
          return (
            <li key={d} className={styles.cell} data-testid={`plot-dim-${d}`}>
              <span className={styles.label}>{label}</span>
              <svg viewBox={`0 0 ${PLOT_W} ${PLOT_H}`} className={styles.svg} role="img" aria-label={`${label} trajectory plot`}>
                <polyline points={points} className={styles.line} fill="none" />
                <line x1={markerX} y1={0} x2={markerX} y2={PLOT_H} className={styles.marker} />
              </svg>
              <span className={styles.value}>{value.toFixed(3)}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
