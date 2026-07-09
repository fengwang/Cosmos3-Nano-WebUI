"use client";

import type { MediaKind } from "@/lib/studio/types";

import styles from "./MediaPreview.module.css";

export interface MediaPreviewProps {
  src: string;
  kind: MediaKind;
  /** Accessible name for the media. */
  label: string;
}

/** Renders conditioning/result media by kind with native controls (img / video / audio). */
export function MediaPreview({ src, kind, label }: MediaPreviewProps) {
  if (kind === "video") {
    return <video className={styles.media} src={src} controls aria-label={label} data-testid="media-video" />;
  }
  if (kind === "audio") {
    return <audio className={styles.audio} src={src} controls aria-label={label} data-testid="media-audio" />;
  }
  // eslint-disable-next-line @next/next/no-img-element -- runtime artifact / object URL, not a static asset; next/image needs loader/domain config out of scope for S9
  return <img className={styles.media} src={src} alt={label} data-testid="media-image" />;
}
