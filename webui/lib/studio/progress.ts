// Progress presentation (ACD: a pure Calculation over the projected JobView). Decides how the progress
// indicator should render without touching wall-clock time or fabricating a percentage (R-08):
//   - indeterminate while the job is non-terminal AND its progress is still exactly 0 — the honest state
//     for sync modes that emit no advancing progress (t2i, forward_dynamics), and for the brief pre-first-
//     event window of any mode;
//   - a real percentage the moment the backend's progress advances above 0 (t2v/i2v/t2v_audio);
//   - never indeterminate once terminal (succeeded resolves to 100%; failed/cancelled resolve too).
// Both job trackers (RunPanel, ActionWorkspace) derive their display from this single calc.

import type { JobView } from "@/lib/studio/jobState";

export interface ProgressDisplay {
  /** Render the animated indeterminate indicator (no numeric %). */
  indeterminate: boolean;
  /** 0..100 for the determinate ring. */
  percent: number;
}

export function describeProgress(view: JobView): ProgressDisplay {
  return {
    indeterminate: !view.terminal && view.progress === 0,
    percent: view.progress * 100,
  };
}
