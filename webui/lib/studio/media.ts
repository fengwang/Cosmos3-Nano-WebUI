// Media-kind helpers (ACD: pure Calculations; compose/inspect/review). Map a MIME/content-type to the
// kind the studio renders; used by the dropzone (validate), Inspect (preview), and Review (playback).

import type { MediaKind } from "@/lib/studio/types";

/** Map a MIME/content-type to a media kind, or null if it isn't a previewable media type. */
export function mediaKindFromMime(mime: string | null | undefined): MediaKind | null {
  if (!mime) return null;
  if (mime.startsWith("image/")) return "image";
  if (mime.startsWith("video/")) return "video";
  if (mime.startsWith("audio/")) return "audio";
  return null;
}

/** The public byte cap for a kind (mirrors api/preprocessing/limits.py defaults). */
export const BYTE_CAPS: Record<MediaKind, number> = {
  image: 32 * 1024 * 1024,
  video: 512 * 1024 * 1024,
  audio: 64 * 1024 * 1024,
};

/** Is a file within the public byte cap for its kind? (Client pre-check before base64 encoding.) */
export function withinByteCap(kind: MediaKind, bytes: number): boolean {
  return bytes <= BYTE_CAPS[kind];
}

/** The artifact kind a generation mode produces: t2i → image; t2v/i2v/t2v_audio → video (audio is muxed). */
export function artifactKindForMode(mode: string): MediaKind {
  return mode === "t2i" ? "image" : "video";
}

/** File extension for a media kind (artifact download filename). */
export const EXT_FOR_KIND: Record<MediaKind, string> = { image: "png", video: "mp4", audio: "wav" };
