"use client";

import { useEffect, useRef, useState } from "react";

import { downsamplePeaks } from "@/lib/studio/waveform";

import styles from "./Waveform.module.css";

const BUCKETS = 160;

/**
 * Audio waveform: decode (Web Audio Action), reduce to peaks (pure `downsamplePeaks`), draw to a canvas.
 * `role="img"` + a label make it announceable; the audio element remains the playback affordance.
 */
export function Waveform({ src, label }: { src: string; label: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [peaks, setPeaks] = useState<number[]>([]);

  useEffect(() => {
    let aborted = false;
    async function decode() {
      let ctx: AudioContext | undefined;
      try {
        const res = await fetch(src);
        const buffer = await res.arrayBuffer();
        if (typeof window === "undefined" || !window.AudioContext) return;
        ctx = new AudioContext();
        const decoded = await ctx.decodeAudioData(buffer);
        if (!aborted) setPeaks(downsamplePeaks(decoded.getChannelData(0), BUCKETS));
      } catch {
        // decoding is best-effort; the <audio> element still plays.
      } finally {
        void ctx?.close();
      }
    }
    void decode();
    return () => {
      aborted = true;
    };
  }, [src]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);
    const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#15795a";
    ctx.fillStyle = accent;
    const bar = width / Math.max(1, peaks.length);
    peaks.forEach((p, i) => {
      const h = Math.max(1, p * height);
      ctx.fillRect(i * bar, (height - h) / 2, Math.max(1, bar - 1), h);
    });
  }, [peaks]);

  return <canvas ref={canvasRef} width={640} height={96} role="img" aria-label={label} className={styles.canvas} />;
}
