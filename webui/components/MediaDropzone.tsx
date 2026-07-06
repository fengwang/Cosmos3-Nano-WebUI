"use client";

import { useId, useRef } from "react";
import type { ChangeEvent } from "react";

import { mediaKindFromMime, withinByteCap } from "@/lib/studio/media";
import type { AttachedMedia } from "@/lib/studio/types";

import styles from "./MediaDropzone.module.css";

export interface MediaDropzoneProps {
  media?: AttachedMedia;
  onAttach: (media: AttachedMedia) => void;
  onClear: () => void;
  onReject: (message: string) => void;
}

/** Read a File to base64 (strip the data: URL prefix) — the only Action here. */
function readBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("file read failed"));
    reader.onload = () => {
      const result = String(reader.result);
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.readAsDataURL(file);
  });
}

/** File picker with client-side MIME/size validation (mirrors the public caps) → base64 InlineMedia. */
export function MediaDropzone({ media, onAttach, onClear, onReject }: MediaDropzoneProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);

  async function onChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const kind = mediaKindFromMime(file.type);
    if (!kind) {
      onReject(`Unsupported file type: ${file.type || "unknown"}.`);
      return;
    }
    if (!withinByteCap(kind, file.size)) {
      onReject(`That ${kind} exceeds the public size limit.`);
      return;
    }
    try {
      const dataBase64 = await readBase64(file);
      onAttach({ kind, mime: file.type, name: file.name, bytes: file.size, dataBase64 });
    } catch {
      onReject("Could not read the selected file.");
    }
  }

  return (
    <div className={styles.zone}>
      <label htmlFor={inputId} className={styles.label}>
        Conditioning media (optional)
      </label>
      <input
        id={inputId}
        ref={inputRef}
        type="file"
        accept="image/*,video/*,audio/*"
        onChange={onChange}
        className={styles.input}
        data-testid="media-input"
      />
      {media ? (
        <div className={styles.attached}>
          <span>
            {media.name} · {media.kind}
          </span>
          <button
            type="button"
            className={styles.remove}
            onClick={() => {
              onClear();
              if (inputRef.current) inputRef.current.value = "";
            }}
          >
            Remove
          </button>
        </div>
      ) : null}
    </div>
  );
}
