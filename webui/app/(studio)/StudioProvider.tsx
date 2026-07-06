"use client";

import { createContext, useCallback, useContext, useEffect, useReducer, useRef, useState } from "react";
import type { Dispatch, ReactNode } from "react";

import { friendlyError } from "@/lib/errors";
import { API_PREFIX, apiFetch } from "@/lib/api/client";
import { createEventStream } from "@/lib/sse/createEventStream";
import { draft as draftReducer, initialDraft } from "@/lib/studio/draft";
import type { DraftAction } from "@/lib/studio/draft";
import { statusLabel } from "@/lib/studio/format";
import { initialJobView, reduceJobEvent } from "@/lib/studio/jobState";
import type { JobView } from "@/lib/studio/jobState";
import { buildRequest } from "@/lib/studio/request";
import type { Draft, Job, Warning } from "@/lib/studio/types";

import { useHistory } from "./useHistory";
import { useLiveRegion } from "./useLiveRegion";

export type Stage = "compose" | "inspect" | "run" | "review";

export interface ActiveJob {
  jobId: string;
  mode: string;
}

interface StudioValue {
  draft: Draft;
  dispatch: Dispatch<DraftAction>;
  stage: Stage;
  setStage: (stage: Stage) => void;
  active: ActiveJob | null;
  view: JobView | null;
  /** True while the job-events stream is dropped and retrying (RK-09 UX cue). */
  jobReconnecting: boolean;
  /** The proxied artifact URL once the active job has succeeded. */
  artifactUrl: string | null;
  submitError: Warning | null;
  submit: () => Promise<void>;
  cancel: () => Promise<void>;
  retry: () => Promise<void>;
  openJob: (jobId: string, mode: string) => void;
  history: ReturnType<typeof useHistory>["entries"];
}

const StudioContext = createContext<StudioValue | null>(null);

export function useStudio(): StudioValue {
  const ctx = useContext(StudioContext);
  if (!ctx) throw new Error("useStudio must be used within <StudioProvider>");
  return ctx;
}

const jobUrl = (id: string, suffix = ""): string => `${API_PREFIX}/v1/jobs/${encodeURIComponent(id)}${suffix}`;

async function safeJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export function StudioProvider({ children }: { children: ReactNode }) {
  const [draft, dispatch] = useReducer(draftReducer, undefined, initialDraft);
  const [stage, setStage] = useState<Stage>("compose");
  const [active, setActive] = useState<ActiveJob | null>(null);
  const [view, setView] = useState<JobView | null>(null);
  const [jobReconnecting, setJobReconnecting] = useState(false);
  const [submitError, setSubmitError] = useState<Warning | null>(null);
  const { entries: history, record } = useHistory();
  const announce = useLiveRegion();

  // Latest draft + the last-submitted snapshot, read by callbacks without stale closures.
  const draftRef = useRef(draft);
  draftRef.current = draft;
  const lastDraftRef = useRef<Draft | null>(null);

  const doSubmit = useCallback(
    async (source: Draft) => {
      setSubmitError(null);
      const { path, body } = buildRequest(source);
      let res: Response;
      try {
        res = await apiFetch(path, {
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
      lastDraftRef.current = source;
      record({ id: job.id, mode: job.mode, summary: source.prompt.slice(0, 80), createdAt: job.created_at });
      setActive({ jobId: job.id, mode: job.mode });
      setView(initialJobView(job.status));
      setStage("run");
    },
    [record],
  );

  const submit = useCallback(() => doSubmit(draftRef.current), [doSubmit]);
  const retry = useCallback(() => doSubmit(lastDraftRef.current ?? draftRef.current), [doSubmit]);

  const cancel = useCallback(async () => {
    const current = active;
    if (!current) return;
    announce("Cancelling job…");
    try {
      const res = await fetch(jobUrl(current.jobId, "/cancel"), { method: "POST" });
      if (res.ok) {
        // Server-confirmed: reflect the cancelled terminal the server returned (never a faked local state).
        setView((prev) => reduceJobEvent(prev ?? initialJobView(), { event: "cancelled", data: "{}" }));
      }
    } catch {
      // The open events stream / poll fallback will still surface the terminal state.
    }
  }, [active, announce]);

  const openJob = useCallback((jobId: string, mode: string) => {
    setActive({ jobId, mode });
    setView(initialJobView("queued"));
    setStage("review");
  }, []);

  // Live job tracking: subscribe to the events SSE while a job is active (RK-09 reconnect + poll fallback
  // live inside createEventStream). The pure projectJob/reduceJobEvent does the state math.
  useEffect(() => {
    if (!active) return;
    setJobReconnecting(false);
    const controller = new AbortController();
    void createEventStream({
      url: jobUrl(active.jobId, "/events"),
      heartbeatTimeoutMs: 30_000,
      signal: controller.signal,
      onEvent: (event) => {
        setJobReconnecting(false);
        setView((prev) => reduceJobEvent(prev ?? initialJobView(), event));
      },
      onError: () => setJobReconnecting(true),
      pollFallback: async () => {
        try {
          const res = await fetch(jobUrl(active.jobId), { cache: "no-store" });
          if (!res.ok) return;
          const job = (await safeJson(res)) as Job | null;
          if (!job) return;
          const data = job.error ? JSON.stringify({ message: job.error.message }) : "{}";
          setView((prev) => reduceJobEvent(prev ?? initialJobView(), { event: job.status, data }));
        } catch {
          // best-effort terminal reconciliation
        }
      },
    });
    return () => controller.abort();
  }, [active]);

  // Announce status transitions through the polite live region (NFR3 / EC-U4).
  const lastStatusRef = useRef<string | null>(null);
  useEffect(() => {
    if (view && view.status !== lastStatusRef.current) {
      lastStatusRef.current = view.status;
      announce(`Job ${statusLabel(view.status)}.`);
    }
  }, [view, announce]);

  const artifactUrl = active && view?.status === "succeeded" ? jobUrl(active.jobId, "/artifact") : null;

  const value: StudioValue = {
    draft,
    dispatch,
    stage,
    setStage,
    active,
    view,
    jobReconnecting,
    artifactUrl,
    submitError,
    submit,
    cancel,
    retry,
    openJob,
    history,
  };

  return <StudioContext.Provider value={value}>{children}</StudioContext.Provider>;
}
