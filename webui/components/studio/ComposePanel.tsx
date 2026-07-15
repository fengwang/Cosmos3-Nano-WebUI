"use client";

import { useState } from "react";

import { useStudio } from "@/app/(studio)/StudioProvider";
import { Banner, WarningList } from "@/components/Banner";
import { MediaDropzone } from "@/components/MediaDropzone";
import { Select } from "@/components/Select";
import { Textarea } from "@/components/Textarea";
import { Card, Input, PillButton } from "@/design-system";
import { compatibleModes, flagImpossible, hasBlockingFlag } from "@/lib/studio/modes";
import { modeLabel } from "@/lib/studio/request";
import type { DraftParams, GenMode } from "@/lib/studio/types";

const VALID_DIMENSIONS = ["256", "480", "640", "720", "960", "1280"];

import styles from "./studio.module.css";

const MODES: GenMode[] = ["t2i", "t2v", "i2v", "t2v_audio"];

function parseIntOrUndef(raw: string): number | undefined {
  const n = parseInt(raw, 10);
  return Number.isNaN(n) ? undefined : n;
}

/** Compose stage: task picker + prompt + upload; live compatibility flags + friendly 422. The served
 * checkpoint is implicit in the deployed stack (S6/FR-12), so there is no checkpoint selector. */
export function ComposePanel() {
  const { draft, dispatch, submit, submitError } = useStudio();
  const [rejected, setRejected] = useState<string | null>(null);
  const flags = flagImpossible(draft);
  const compatible = compatibleModes(draft.media?.mime ?? null);
  const blocked = hasBlockingFlag(flags) || draft.prompt.trim().length === 0;

  const setParam = (key: keyof DraftParams, raw: string) =>
    dispatch({ type: "setParam", key, value: parseIntOrUndef(raw) });

  return (
    <Card title="Compose">
      <div className={styles.stack}>
        <fieldset className={styles.group}>
          <legend className={styles.legend}>Task</legend>
          <div className={styles.row}>
            {MODES.map((m) => (
              <PillButton
                key={m}
                selected={draft.mode === m}
                onClick={() => dispatch({ type: "setMode", mode: m })}
                data-testid={`mode-${m}`}
              >
                {modeLabel(m)}
              </PillButton>
            ))}
          </div>
          <p className={styles.hint}>
            {draft.media ? `Compatible with your ${draft.media.kind}: ` : "Without media: "}
            {compatible.length ? compatible.map(modeLabel).join(", ") : "none"}
          </p>
        </fieldset>

        <Textarea
          label="Prompt"
          value={draft.prompt}
          placeholder="Describe the scene to generate…"
          onChange={(e) => dispatch({ type: "setPrompt", value: e.target.value })}
          data-testid="prompt"
        />
        <Input
          label="Negative prompt (optional)"
          placeholder="Using recommended default"
          value={draft.negativePrompt ?? ""}
          onChange={(e) => dispatch({ type: "setNegative", value: e.target.value })}
        />

        <details data-testid="generation-settings">
          <summary className={styles.legend}>Generation settings</summary>
          <div className={styles.stack}>
            <div className={styles.row}>
              <Select
                label="Height"
                value={String(draft.params.height ?? "")}
                onChange={(e) => setParam("height", e.target.value)}
                options={VALID_DIMENSIONS.map((v) => ({ value: v, label: `${v}px` }))}
                data-testid="param-height"
              />
              <Select
                label="Width"
                value={String(draft.params.width ?? "")}
                onChange={(e) => setParam("width", e.target.value)}
                options={VALID_DIMENSIONS.map((v) => ({ value: v, label: `${v}px` }))}
                data-testid="param-width"
              />
            </div>
            <div className={styles.row}>
              <Input
                label="Frames"
                type="number"
                min={1}
                max={720}
                value={draft.params.num_frames ?? ""}
                onChange={(e) => setParam("num_frames", e.target.value)}
                data-testid="param-frames"
              />
              <Input
                label="Steps"
                type="number"
                min={1}
                max={50}
                value={draft.params.num_inference_steps ?? ""}
                onChange={(e) => setParam("num_inference_steps", e.target.value)}
                data-testid="param-steps"
              />
            </div>
            <div className={styles.row}>
              <Input
                label="Seed"
                type="number"
                min={0}
                value={draft.params.seed ?? 123}
                onChange={(e) => setParam("seed", e.target.value)}
                data-testid="param-seed"
              />
              <PillButton
                onClick={() => dispatch({ type: "setParam", key: "seed", value: Math.floor(Math.random() * 2147483647) })}
                data-testid="randomize-seed"
              >
                ↻
              </PillButton>
            </div>
          </div>
        </details>

        <MediaDropzone
          media={draft.media}
          onAttach={(m) => {
            setRejected(null);
            dispatch({ type: "attachMedia", media: m });
          }}
          onClear={() => dispatch({ type: "clearMedia" })}
          onReject={setRejected}
        />
        {rejected ? <Banner severity="error">{rejected}</Banner> : null}

        <WarningList warnings={flags} />
        {submitError ? <Banner severity="error">{submitError.message}</Banner> : null}

        <div className={styles.row}>
          <PillButton tone="accent" onClick={() => void submit()} disabled={blocked} data-testid="generate">
            Generate →
          </PillButton>
        </div>
      </div>
    </Card>
  );
}
