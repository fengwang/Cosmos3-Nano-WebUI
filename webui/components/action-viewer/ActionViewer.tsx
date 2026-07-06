"use client";

import { useEffect, useRef, useState } from "react";

import type { JointMap } from "./jointmap";
import { buildPose } from "./pose";
import { normalizedTime, sampleIndex } from "./sync";
import { createURDFScene } from "./URDFScene";
import type { URDFScene } from "./URDFScene";
import styles from "./ActionViewer.module.css";

export interface ActionViewerProps {
  /** A LOCAL urdf path (e.g. `/urdf/agibotworld.urdf`). */
  urdfUrl: string;
  jointMap: JointMap;
  /** The trajectory to animate ([T][width]) — predicted (policy) or the input driving tensor (FD). */
  trajectory: number[][];
  /** The rollout video (the master clock when it has a real duration; else the scrub drives the timeline). */
  videoUrl?: string | null;
  /** Controlled normalized timeline position [0,1] — shared with the plots/inspection current-frame marker. */
  normalizedT: number;
  /** Reports the timeline up (on scrub, and — throttled to frame changes — while the video plays). */
  onTimeChange: (t: number) => void;
  onError?: (message: string) => void;
}

/**
 * The WebGL viewer (client-only; imported via `next/dynamic({ ssr:false })`). It owns the canvas + a synced
 * video + a keyboard-operable timeline scrub, and on every animation frame samples the trajectory (pure)
 * and applies the pose to the URDFScene. The timeline is CONTROLLED by `normalizedT` so the 3D pose, the
 * video, the 2D plots, and the inspection frame readout all move together. The pose is mirrored to
 * `data-joint-values` so the headless smoke can assert that scrubbing moves the joints (no real playback).
 */
export default function ActionViewer({
  urdfUrl,
  jointMap,
  trajectory,
  videoUrl,
  normalizedT,
  onTimeChange,
  onError,
}: ActionViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const trajRef = useRef(trajectory);
  trajRef.current = trajectory;
  const mapRef = useRef(jointMap);
  mapRef.current = jointMap;
  const normRef = useRef(normalizedT);
  normRef.current = normalizedT;
  const onTimeRef = useRef(onTimeChange);
  onTimeRef.current = onTimeChange;
  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;
  const lastIdxRef = useRef(-1);
  const [ready, setReady] = useState(false);

  // Scene lifecycle + the animation loop. Depends only on urdfUrl so a trajectory change never re-creates
  // the WebGL context (the loop reads trajRef/mapRef/normRef).
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let scene: URDFScene;
    try {
      scene = createURDFScene(canvas);
    } catch (err) {
      onErrorRef.current?.(err instanceof Error ? err.message : "WebGL is unavailable in this browser.");
      return;
    }

    let raf = 0;
    let cancelled = false;
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      scene.setSize(rect.width || 480, rect.height || 360);
    };
    resize();
    window.addEventListener("resize", resize);

    scene
      .load(urdfUrl)
      .then(({ jointNames }) => {
        if (cancelled) return;
        // Seam-level joint-existence check against the REAL URDF (RK-04 config↔URDF drift guard): if the
        // map references a joint the loaded robot lacks, bail to the 2D fallback instead of a silent no-op.
        const missing = mapRef.current.joints.filter((j) => !jointNames.includes(j.joint));
        if (missing.length > 0) {
          onErrorRef.current?.(`URDF is missing mapped joints: ${missing.map((m) => m.joint).join(", ")}`);
          return;
        }
        setReady(true);
        const loop = () => {
          if (cancelled) return;
          const frames = trajRef.current;
          const T = frames.length;
          const video = videoRef.current;
          const videoDrives = !!video && Number.isFinite(video.duration) && video.duration > 0;
          const t = videoDrives ? normalizedTime(video.currentTime, video.duration) : normRef.current;
          const sample = sampleIndex(t, T);
          if (T > 0) {
            const pose = buildPose(frames, mapRef.current, sample);
            scene.setJointValues(pose.joints);
            for (const o of pose.orientations) scene.setOrientation(o.link, o.quat);
            if (sample.i0 !== lastIdxRef.current) {
              lastIdxRef.current = sample.i0;
              canvas.dataset.jointValues = JSON.stringify(pose.joints);
              canvas.dataset.frame = String(sample.i0);
              if (videoDrives) onTimeRef.current(t); // keep the shared marker tracking during playback
            }
          }
          scene.render();
          raf = requestAnimationFrame(loop);
        };
        raf = requestAnimationFrame(loop);
      })
      .catch((err: unknown) => {
        if (!cancelled) onErrorRef.current?.(err instanceof Error ? err.message : "The URDF failed to load.");
      });

    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      scene.dispose();
    };
  }, [urdfUrl]);

  const onScrub = (value: number): void => {
    const t = value / 1000;
    onTimeRef.current(t);
    const video = videoRef.current;
    if (video && Number.isFinite(video.duration) && video.duration > 0) {
      video.currentTime = t * video.duration;
    }
  };

  return (
    <div className={styles.viewer} data-testid="action-viewer">
      <div className={styles.stage}>
        <canvas
          ref={canvasRef}
          className={styles.canvas}
          data-testid="action-canvas"
          role="img"
          aria-label="3D kinematic view of the robot following the action trajectory"
        />
        {!ready ? (
          <p className={styles.status} role="status">
            Loading 3D view…
          </p>
        ) : null}
      </div>
      {videoUrl ? (
        <video
          ref={videoRef}
          className={styles.video}
          src={videoUrl}
          controls
          aria-label="Generated rollout video"
          data-testid="action-video"
        />
      ) : null}
      <label className={styles.scrub}>
        <span>Timeline</span>
        <input
          type="range"
          min={0}
          max={1000}
          value={Math.round(normalizedT * 1000)}
          onChange={(e) => onScrub(Number(e.target.value))}
          data-testid="action-scrub"
          aria-label="Trajectory timeline position"
        />
      </label>
    </div>
  );
}
