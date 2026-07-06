"use client";

import { useState } from "react";

import { useStudio } from "@/app/(studio)/StudioProvider";
import { MediaPreview } from "@/components/MediaPreview";
import { Select } from "@/components/Select";
import { Card } from "@/design-system";
import { API_PREFIX } from "@/lib/api/client";
import { artifactKindForMode, EXT_FOR_KIND } from "@/lib/studio/media";

import styles from "./studio.module.css";

/** Review stage: playback, export/download, side-by-side compare, and structured output if present. */
export function ReviewPanel() {
  const { active, view, artifactUrl, history } = useStudio();
  const [compareId, setCompareId] = useState("");

  if (!active || view?.status !== "succeeded" || !artifactUrl) {
    return (
      <Card title="Review">
        <p className={styles.hint}>Run a job to review its result here.</p>
      </Card>
    );
  }

  const kind = artifactKindForMode(active.mode);
  const meta = view.meta ?? {};
  const others = history.filter((h) => h.id !== active.jobId);
  const compareEntry = others.find((h) => h.id === compareId);

  return (
    <Card title="Review">
      <div className={styles.stack}>
        <div className={compareEntry ? styles.compareGrid : undefined}>
          <figure className={styles.stackTight}>
            <MediaPreview src={artifactUrl} kind={kind} label={`Result for ${active.mode}`} />
            <figcaption className={styles.hint}>Current · {active.mode}</figcaption>
          </figure>
          {compareEntry ? (
            <figure className={styles.stackTight}>
              <MediaPreview
                src={`${API_PREFIX}/v1/jobs/${encodeURIComponent(compareEntry.id)}/artifact`}
                kind={artifactKindForMode(compareEntry.mode)}
                label={`Comparison for ${compareEntry.mode}`}
              />
              <figcaption className={styles.hint}>Compare · {compareEntry.mode}</figcaption>
            </figure>
          ) : null}
        </div>

        <div className={styles.row}>
          <a
            className={styles.download}
            href={artifactUrl}
            download={`cosmos3-${active.jobId}.${EXT_FOR_KIND[kind]}`}
            data-testid="download"
          >
            Download artifact
          </a>
        </div>

        {Object.keys(meta).length > 0 ? (
          <dl className={styles.meta} data-testid="result-meta">
            {Object.entries(meta).map(([k, val]) => (
              <div key={k} className={styles.row}>
                <dt>{k}</dt>
                <dd>{String(val)}</dd>
              </div>
            ))}
          </dl>
        ) : null}

        {others.length > 0 ? (
          <Select
            label="Compare with a past job"
            value={compareId}
            onChange={(e) => setCompareId(e.target.value)}
            options={[
              { value: "", label: "None" },
              ...others.map((h) => ({ value: h.id, label: `${h.mode} · ${h.summary || h.id}` })),
            ]}
          />
        ) : null}
      </div>
    </Card>
  );
}
