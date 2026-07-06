"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { API_PREFIX, apiFetch } from "@/lib/api/client";
import { friendlyError } from "@/lib/errors";
import { createEventStream } from "@/lib/sse/createEventStream";
import { initialJobView, reduceJobEvent } from "@/lib/studio/jobState";
import type { JobView } from "@/lib/studio/jobState";
import type { components } from "@/lib/api/schema";
import type { Job, Warning } from "@/lib/studio/types";

import { parseTrajectory } from "./trajectory";

export type ActionMode = "forward_dynamics" | "inverse_dynamics" | "policy";
export type ActionBody = components["schemas"]["ActionBody"];

/** The typed action submit paths (literals → valid ApiPath; template strings are not). */
const ACTION_PATHS: Record<ActionMode, "/v1/action/forward_dynamics" | "/v1/action/inverse_dynamics" | "/v1/action/policy"> = {
  forward_dynamics: "/v1/action/forward_dynamics",
  inverse_dynamics: "/v1/action/inverse_dynamics",
  policy: "/v1/action/policy",
};

const jobUrl = (id: string, suffix = ""): string => `${API_PREFIX}/v1/jobs/${encodeURIComponent(id)}${suffix}`;

async function safeJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export interface ActiveActionJob {
  id: string;
  mode: string;
  domain: string;
}

export interface UseActionJob {
  view: JobView | null;
  active: ActiveActionJob | null;
  /** Proxied rollout-video URL once the job succeeds (FD/policy). */
  artifactUrl: string | null;
  /** The trajectory to visualize: the FD input (retained) or the predicted ID/policy trajectory (fetched). */
  trajectory: number[][] | null;
  reconnecting: boolean;
  submitError: Warning | null;
  submit: (mode: ActionMode, body: ActionBody, inputTrajectory?: number[][]) => Promise<void>;
  openJob: (id: string, mode: string, domain: string) => void;
  cancel: () => Promise<void>;
  reset: () => void;
}

/**
 * Action job controller. Submits to `/v1/action/{mode}` and tracks the job by feeding the events SSE through
 * the REUSED pure `reduceJobEvent` (INV-5/RK-09). On success it resolves the trajectory: the retained FD
 * input, or — for ID/policy — the `…/trajectory` sidecar (falling back to a JSON `…/artifact`). No edit to
 * `StudioProvider`; the proven job logic is reused by import.
 */
export function useActionJob(): UseActionJob {
  const [view, setView] = useState<JobView | null>(null);
  const [active, setActive] = useState<ActiveActionJob | null>(null);
  const [trajectory, setTrajectory] = useState<number[][] | null>(null);
  const [reconnecting, setReconnecting] = useState(false);
  const [submitError, setSubmitError] = useState<Warning | null>(null);
  const trajectoryRef = useRef<number[][] | null>(null);
  trajectoryRef.current = trajectory;

  const reset = useCallback(() => {
    setActive(null);
    setView(null);
    setTrajectory(null);
    setReconnecting(false);
    setSubmitError(null);
  }, []);

  const submit = useCallback(async (mode: ActionMode, body: ActionBody, inputTrajectory?: number[][]) => {
    setSubmitError(null);
    let res: Response;
    try {
      res = await apiFetch(ACTION_PATHS[mode], {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch {
      setSubmitError(friendlyError(0, { message: "Could not reach the API. Check the connection and retry." }));
      return;
    }
    if (res.status !== 202) {
      setSubmitError(friendlyError(res.status, await safeJson(res)));
      return;
    }
    const job = (await safeJson(res)) as Job | null;
    if (!job) {
      setSubmitError(friendlyError(res.status, { message: "The server accepted the job but returned no id." }));
      return;
    }
    // Only on a confirmed 202 do we adopt the job + its trajectory. FD: the actions ARE the input — retain
    // them to animate; ID/policy fetch the predicted trajectory on success. (A failed submit leaves no
    // phantom trajectory rendered.)
    setTrajectory(inputTrajectory ?? null);
    setActive({ id: job.id, mode: job.mode, domain: body.domain_name });
    setView(initialJobView(job.status));
  }, []);

  const openJob = useCallback((id: string, mode: string, domain: string) => {
    setSubmitError(null);
    setTrajectory(null);
    setActive({ id, mode, domain });
    setView(initialJobView("queued"));
  }, []);

  const cancel = useCallback(async () => {
    if (!active) return;
    try {
      const res = await fetch(jobUrl(active.id, "/cancel"), { method: "POST" });
      if (res.ok) setView((prev) => reduceJobEvent(prev ?? initialJobView(), { event: "cancelled", data: "{}" }));
    } catch {
      // the open events stream / poll fallback still surfaces the terminal state
    }
  }, [active]);

  // Live job tracking — reuse the reconnecting SSE client + the pure event fold (RK-09).
  useEffect(() => {
    if (!active) return;
    setReconnecting(false);
    const controller = new AbortController();
    void createEventStream({
      url: jobUrl(active.id, "/events"),
      heartbeatTimeoutMs: 30_000,
      signal: controller.signal,
      onEvent: (event) => {
        setReconnecting(false);
        setView((prev) => reduceJobEvent(prev ?? initialJobView(), event));
      },
      onError: () => setReconnecting(true),
      pollFallback: async () => {
        try {
          const res = await fetch(jobUrl(active.id), { cache: "no-store" });
          if (!res.ok) return;
          const job = (await safeJson(res)) as Job | null;
          if (!job) return;
          const data = job.error ? JSON.stringify({ message: job.error.message }) : "{}";
          setView((prev) => reduceJobEvent(prev ?? initialJobView(), { event: job.status, data }));
        } catch {
          // best-effort reconciliation
        }
      },
    });
    return () => controller.abort();
  }, [active]);

  // On success, resolve the trajectory to visualize (skip if the FD input is already retained).
  useEffect(() => {
    if (!active || view?.status !== "succeeded" || trajectoryRef.current) return;
    let cancelled = false;
    void (async () => {
      for (const suffix of ["/trajectory", "/artifact"]) {
        try {
          const res = await fetch(jobUrl(active.id, suffix), { cache: "no-store" });
          if (!res.ok) continue;
          if (!(res.headers.get("content-type") ?? "").includes("json")) continue; // a video artifact is not json
          const data = await safeJson(res);
          const parsed = parseTrajectory(data);
          if (!cancelled) setTrajectory(parsed.frames);
          return;
        } catch {
          // try the next source
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [active, view?.status]);

  const artifactUrl = active && view?.status === "succeeded" ? jobUrl(active.id, "/artifact") : null;

  return { view, active, artifactUrl, trajectory, reconnecting, submitError, submit, openJob, cancel, reset };
}
