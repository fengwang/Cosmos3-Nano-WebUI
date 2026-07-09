// Job-state projection (ACD: pure fold over SSE events; run, INV-5/RK-09). Maps the api's REAL job-event
// types — running / progress{progress} / heartbeat / succeeded{meta} / failed{message} / cancelled — plus
// a forward-compatible `warning` event (the api has no warning channel yet; filed to S7) into an inert
// view the tracker renders. The live subscription (createEventStream) is the Action; this is the Calc.

import type { SseEvent } from "@/lib/sse/parseSse";
import type { JobStatus, Warning } from "@/lib/studio/types";

export interface JobView {
  status: JobStatus | "submitting";
  progress: number; // 0..1
  warnings: Warning[];
  error?: Warning;
  terminal: boolean;
  meta?: Record<string, unknown>;
}

export function initialJobView(status: JobView["status"] = "queued"): JobView {
  return { status, progress: 0, warnings: [], terminal: false };
}

function parse(data: string): Record<string, unknown> {
  try {
    const value: unknown = JSON.parse(data);
    return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

const clamp01 = (n: number): number => (n < 0 ? 0 : n > 1 ? 1 : n);

/** Reduce one SSE event into the view (pure). Unknown/heartbeat events are no-ops. */
export function reduceJobEvent(view: JobView, ev: SseEvent): JobView {
  const d = parse(ev.data);
  switch (ev.event) {
    case "running":
      return view.terminal ? view : { ...view, status: "running" };
    case "progress": {
      const p = typeof d.progress === "number" ? clamp01(d.progress) : view.progress;
      return view.terminal ? { ...view, progress: p } : { ...view, status: "running", progress: p };
    }
    case "succeeded":
      return { ...view, status: "succeeded", progress: 1, terminal: true, meta: d };
    case "failed":
      return {
        ...view,
        status: "failed",
        terminal: true,
        error: {
          severity: "error",
          code: "job_failed",
          message: typeof d.message === "string" && d.message ? d.message : "The job failed.",
        },
      };
    case "cancelled":
      return { ...view, status: "cancelled", terminal: true };
    case "warning":
      return {
        ...view,
        warnings: [
          ...view.warnings,
          {
            severity: "warn",
            code: typeof d.code === "string" ? d.code : "warning",
            message: typeof d.message === "string" ? d.message : "Warning.",
          },
        ],
      };
    default:
      return view; // heartbeat / unknown
  }
}

/** Fold a batch of events onto a seed view. */
export function projectJob(events: SseEvent[], seed: JobView = initialJobView()): JobView {
  return events.reduce(reduceJobEvent, seed);
}
