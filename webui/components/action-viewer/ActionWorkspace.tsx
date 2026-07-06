"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

import { Banner } from "@/components/Banner";
import { Select } from "@/components/Select";
import { StatusBadge } from "@/components/StatusBadge";
import { ProgressRing } from "@/design-system";
import { formatElapsed } from "@/lib/studio/format";
import { describeProgress } from "@/lib/studio/progress";
import { useElapsed } from "@/lib/studio/useElapsed";

import { canonicalWidthOf, viewerModeFor } from "./embodiments";
import { demoTrajectory } from "./fixture";
import { EMBODIMENT_JOINT_MAPS, validateJointMap } from "./jointmap";
import type { JointMap } from "./jointmap";
import { currentFrame } from "./sync";
import { decideViewer } from "./viewerDecision";
import { InspectionPanel } from "./InspectionPanel";
import { TrajectoryPlots } from "./TrajectoryPlots";
import { useActionJob } from "./useActionJob";
import type { ActionBody, ActionMode } from "./useActionJob";
import { DEMO_CHUNK, demoActionBody } from "./demoBody";
import styles from "./ActionWorkspace.module.css";

// Client-only WebGL viewer: not in the studio/chat bundles and never server-rendered (WebGL needs a DOM).
const ActionViewer = dynamic(() => import("./ActionViewer"), {
  ssr: false,
  loading: () => (
    <p role="status" className={styles.loading}>
      Loading 3D view…
    </p>
  ),
});

const URDF_FOR: Record<string, string> = { agibotworld: "/urdf/agibotworld.urdf" };

// The S4-verified set + the modes each proved (agibotworld FD/policy; av ID). The api still validates.
const MODE_OPTIONS: Record<string, { value: ActionMode; label: string }[]> = {
  agibotworld: [
    { value: "policy", label: "Policy" },
    { value: "forward_dynamics", label: "Forward dynamics" },
  ],
  av: [{ value: "inverse_dynamics", label: "Inverse dynamics" }],
};

function buildLabels(map: JointMap | undefined, width: number): string[] {
  const labels = Array.from({ length: width }, (_, d) => `dim ${d}`);
  if (!map) return labels;
  for (const j of map.joints) if (j.dim < width) labels[j.dim] = j.joint;
  const comps = ["qx", "qy", "qz", "qw"];
  for (const g of map.orientation ?? []) {
    g.dims.forEach((dim, i) => {
      if (dim < width) labels[dim] = `${g.link}.${comps[i] ?? "q"}`;
    });
  }
  return labels;
}

/**
 * The /action workspace: a minimal entry (pick embodiment/mode + run a demo, or load a job id), the job
 * tracker, and the viewer region. The 3D ActionViewer renders ONLY for a verified embodiment whose
 * joint-map validates; otherwise (and for `av`) the 2D plots are the authoritative view (with a reason).
 */
export function ActionWorkspace() {
  const job = useActionJob();
  const [domainSel, setDomainSel] = useState("agibotworld");
  const [modeSel, setModeSel] = useState<ActionMode>("policy");
  const [jobIdInput, setJobIdInput] = useState("");
  const [normalizedT, setNormalizedT] = useState(0);
  const [viewerError, setViewerError] = useState<string | null>(null);
  const [visibleDims, setVisibleDims] = useState<boolean[]>([]);

  const { active, view, trajectory, artifactUrl, reconnecting, submitError } = job;
  // Degrade progress to indeterminate for forward_dynamics (sync, emits no advancing progress) — never a
  // stuck 0% — and keep an elapsed readout + a Cancel control while non-terminal (FR-9, R-08).
  const elapsed = useElapsed(active?.id, view?.terminal ?? false);
  const progress = view ? describeProgress(view) : null;
  const viewerDomain = active?.domain ?? "";
  const width = trajectory && trajectory.length > 0 ? trajectory[0].length : canonicalWidthOf(viewerDomain) ?? 0;
  const map = viewerDomain ? EMBODIMENT_JOINT_MAPS[viewerDomain] : undefined;
  const configError = map ? validateJointMap(map, canonicalWidthOf(viewerDomain) ?? width, map.joints.map((j) => j.joint)) : null;
  const labels = buildLabels(map, width);
  const frameIdx = currentFrame(normalizedT, trajectory?.length ?? 0);

  const { show3D, reason } = decideViewer({
    domain: viewerDomain,
    hasTrajectory: !!trajectory && trajectory.length > 0,
    trajectoryWidth: trajectory && trajectory.length > 0 ? trajectory[0].length : 0,
    canonicalWidth: canonicalWidthOf(viewerDomain),
    mode: viewerModeFor(viewerDomain),
    hasMap: !!map,
    hasUrdf: !!URDF_FOR[viewerDomain],
    configError,
    viewerError,
  });

  // Reset per-dim visibility + the timeline when the trajectory shape changes.
  useEffect(() => {
    setVisibleDims(Array.from({ length: width }, () => true));
    setNormalizedT(0);
    setViewerError(null);
  }, [width, active?.id]);

  // Announce job status through the root polite live region (NFR3).
  const lastStatus = useRef<string | null>(null);
  useEffect(() => {
    if (view && view.status !== lastStatus.current) {
      lastStatus.current = view.status;
      const region = typeof document !== "undefined" ? document.getElementById("live-region") : null;
      if (region) region.textContent = `Action job ${view.status}.`;
    }
  }, [view]);

  const onDomainChange = (value: string) => {
    setDomainSel(value);
    const first = MODE_OPTIONS[value]?.[0]?.value ?? "policy";
    setModeSel(first);
  };

  const onRunDemo = (e: React.FormEvent) => {
    e.preventDefault();
    const w = canonicalWidthOf(domainSel) ?? 0;
    const body: ActionBody = demoActionBody(domainSel);
    if (modeSel === "forward_dynamics") {
      const quatDims = EMBODIMENT_JOINT_MAPS[domainSel]?.orientation?.[0]?.dims; // derive from the map (single source of truth)
      const raw = demoTrajectory(w, DEMO_CHUNK, quatDims);
      body.raw_actions = raw;
      void job.submit(modeSel, body, raw); // FD: the actions ARE the input → animate them
    } else {
      if (modeSel === "policy") body.prompt = "demo: manipulate the object";
      void job.submit(modeSel, body);
    }
  };

  const onLoad = (e: React.FormEvent) => {
    e.preventDefault();
    const id = jobIdInput.trim();
    if (!id) return;
    const mode = MODE_OPTIONS[domainSel]?.[0]?.value ?? "policy";
    job.openJob(id, mode, domainSel);
  };

  return (
    <div className={styles.workspace}>
      <div className={styles.controls}>
        <form className={styles.entry} onSubmit={onRunDemo} aria-label="Run a demo action job">
          <Select
            label="Embodiment"
            value={domainSel}
            onChange={(e) => onDomainChange(e.target.value)}
            options={[
              { value: "agibotworld", label: "agibotworld (29-D, 3D)" },
              { value: "av", label: "av (9-D, 2D plots)" },
            ]}
          />
          <Select
            label="Mode"
            value={modeSel}
            onChange={(e) => setModeSel(e.target.value as ActionMode)}
            options={MODE_OPTIONS[domainSel] ?? []}
          />
          <button type="submit" className={styles.run}>
            Run demo
          </button>
        </form>
        <form className={styles.entry} onSubmit={onLoad} aria-label="Load an existing action job">
          <label className={styles.field}>
            <span>Job id</span>
            <input
              value={jobIdInput}
              onChange={(e) => setJobIdInput(e.target.value)}
              data-testid="job-id-input"
              placeholder="job_…"
            />
          </label>
          <button type="submit" className={styles.run}>
            Load job
          </button>
        </form>
      </div>

      {submitError ? <Banner severity="error">{submitError.message}</Banner> : null}

      {view && progress ? (
        <div className={styles.statusRow} data-testid="action-status">
          <StatusBadge status={view.status} />
          <ProgressRing
            indeterminate={progress.indeterminate}
            value={progress.percent}
            label="Action progress"
            size={48}
          />
          <span className={styles.elapsed} data-testid="action-elapsed">
            Elapsed {formatElapsed(elapsed)}
          </span>
          {!view.terminal ? (
            <button
              type="button"
              className={styles.cancel}
              onClick={() => void job.cancel()}
              data-testid="action-cancel"
            >
              Cancel
            </button>
          ) : null}
          {reconnecting ? (
            <span role="status" className={styles.reconnect}>
              Reconnecting…
            </span>
          ) : null}
        </div>
      ) : null}

      {view?.error ? <Banner severity="error">{view.error.message}</Banner> : null}

      {trajectory ? (
        <div className={styles.viewerRegion}>
          {show3D && map ? (
            <ActionViewer
              urdfUrl={URDF_FOR[viewerDomain]}
              jointMap={map}
              trajectory={trajectory}
              videoUrl={artifactUrl}
              normalizedT={normalizedT}
              onTimeChange={setNormalizedT}
              onError={setViewerError}
            />
          ) : null}
          <TrajectoryPlots
            frames={trajectory}
            width={width}
            visibleDims={visibleDims}
            currentFrame={frameIdx}
            labels={labels}
            reason={reason}
          />
          <InspectionPanel
            domain={viewerDomain || "—"}
            T={trajectory.length}
            width={width}
            fps={16}
            chunkSize={trajectory.length}
            currentFrame={frameIdx}
            visibleDims={visibleDims}
            labels={labels}
            note={show3D && map ? map.convention : undefined}
            onToggleDim={(d) => setVisibleDims((prev) => prev.map((v, i) => (i === d ? !v : v)))}
          />
        </div>
      ) : view?.status === "succeeded" ? (
        <p className={styles.empty}>This job produced no trajectory to visualize.</p>
      ) : null}
    </div>
  );
}
