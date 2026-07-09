"use client";

import { useStudio } from "@/app/(studio)/StudioProvider";
import { Banner, WarningList } from "@/components/Banner";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, PillButton, ProgressRing } from "@/design-system";
import { formatElapsed } from "@/lib/studio/format";
import { initialJobView } from "@/lib/studio/jobState";
import { describeProgress } from "@/lib/studio/progress";
import { useElapsed } from "@/lib/studio/useElapsed";

import styles from "./studio.module.css";

/** Run stage: async job tracker — SSE progress (indeterminate when unreadable), elapsed time,
 * cancel/retry, warnings/errors (INV-5/RK-09; FR-9). */
export function RunPanel() {
  const { active, view, jobReconnecting, submit, cancel, retry, submitError, draft } = useStudio();
  const jobId = active?.jobId;
  const terminal = view?.terminal ?? false;
  const elapsed = useElapsed(jobId, terminal);

  if (!active) {
    return (
      <Card title="Run">
        <div className={styles.stack}>
          <p className={styles.hint}>Compose a request, then generate. Progress streams here.</p>
          <PillButton
            tone="accent"
            onClick={() => void submit()}
            disabled={draft.prompt.trim().length === 0}
            data-testid="generate-run"
          >
            Generate →
          </PillButton>
          {submitError ? <Banner severity="error">{submitError.message}</Banner> : null}
        </div>
      </Card>
    );
  }

  const v = view ?? initialJobView();
  // Degrade to an indeterminate ring when progress is unreadable (e.g. the sync t2i mode) — never a
  // stuck 0%; the real percentage shows the instant the backend's progress advances (FR-9, R-08).
  const progress = describeProgress(v);
  return (
    <Card title="Run">
      <div className={styles.stack}>
        <div className={styles.row}>
          <StatusBadge status={v.status} />
          <span className={styles.hint}>Job {active.jobId}</span>
        </div>
        <ProgressRing
          indeterminate={progress.indeterminate}
          value={progress.percent}
          label="Generation progress"
        />
        <p className={styles.hint} data-testid="elapsed">
          Elapsed {formatElapsed(elapsed)}
        </p>
        {jobReconnecting && !v.terminal ? (
          <p className={styles.hint} data-testid="job-reconnecting" role="status">
            Connection dropped — reconnecting…
          </p>
        ) : null}
        <div className={styles.row}>
          {!v.terminal ? (
            <PillButton tone="danger" onClick={() => void cancel()} data-testid="cancel">
              Cancel
            </PillButton>
          ) : null}
          {v.terminal && v.status !== "succeeded" ? (
            <PillButton tone="accent" onClick={() => void retry()} data-testid="retry">
              Retry
            </PillButton>
          ) : null}
        </div>
        {v.error ? <Banner severity="error">{v.error.message}</Banner> : null}
        <WarningList warnings={v.warnings} />
      </div>
    </Card>
  );
}
