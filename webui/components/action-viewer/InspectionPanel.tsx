"use client";

import styles from "./InspectionPanel.module.css";

export interface InspectionPanelProps {
  domain: string;
  /** Trajectory length (frames). */
  T: number;
  /** Trajectory width (dims). */
  width: number;
  /** Playback fps (metadata only; the api encodes rollouts at 16). */
  fps: number;
  /** The action transition window (chunk_size), when known. */
  chunkSize?: number;
  /** Current frame index (the shared timeline). */
  currentFrame: number;
  /** Per-dim visibility (index = dim). */
  visibleDims: boolean[];
  labels?: string[];
  /** An advisory note (e.g. the RK-04 candidate-convention caveat), shown when the 3D view is active. */
  note?: string;
  onToggleDim: (dim: number) => void;
}

/** Per-dimension toggles + embodiment metadata (shape / fps / chunk) + the current-frame readout. */
export function InspectionPanel({
  domain,
  T,
  width,
  fps,
  chunkSize,
  currentFrame,
  visibleDims,
  labels,
  note,
  onToggleDim,
}: InspectionPanelProps) {
  const dims = Array.from({ length: width }, (_, d) => d);
  return (
    <section className={styles.panel} aria-label="Inspection" data-testid="inspection-panel">
      <dl className={styles.meta}>
        <div>
          <dt>Embodiment</dt>
          <dd data-testid="meta-domain">{domain}</dd>
        </div>
        <div>
          <dt>Shape</dt>
          <dd data-testid="meta-shape">{T} × {width}</dd>
        </div>
        <div>
          <dt>FPS</dt>
          <dd data-testid="meta-fps">{fps}</dd>
        </div>
        <div>
          <dt>Frame</dt>
          <dd data-testid="meta-frame">
            {Math.min(Math.max(currentFrame, 0), Math.max(T - 1, 0))} / {Math.max(T - 1, 0)}
          </dd>
        </div>
        {chunkSize ? (
          <div>
            <dt>Chunk</dt>
            <dd data-testid="meta-chunk">{chunkSize}</dd>
          </div>
        ) : null}
      </dl>
      {note ? (
        <p className={styles.note} data-testid="mapping-note">
          {note}
        </p>
      ) : null}
      <fieldset className={styles.toggles}>
        <legend>Dimensions</legend>
        <div className={styles.toggleGrid}>
          {dims.map((d) => (
            <label key={d} className={styles.toggle}>
              <input
                type="checkbox"
                checked={visibleDims[d] !== false}
                onChange={() => onToggleDim(d)}
                data-testid={`toggle-dim-${d}`}
              />
              <span>{labels?.[d] ?? `dim ${d}`}</span>
            </label>
          ))}
        </div>
      </fieldset>
    </section>
  );
}
