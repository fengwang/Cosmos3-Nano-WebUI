"use client";

import { useStudio } from "@/app/(studio)/StudioProvider";
import { WarningList } from "@/components/Banner";
import { MediaPreview } from "@/components/MediaPreview";
import { Waveform } from "@/components/Waveform";
import { Card, PillButton } from "@/design-system";
import { advisoriesFor } from "@/lib/studio/advisories";
import { PRESET_LIST } from "@/lib/studio/presets";

import styles from "./studio.module.css";

/** Inspect stage: normalized previews (frames/waveform) + parameter presets + RK-08 advisories. */
export function InspectPanel() {
  const { draft, dispatch } = useStudio();
  const advisories = advisoriesFor(draft);
  const media = draft.media;
  const dataUrl = media ? `data:${media.mime};base64,${media.dataBase64}` : null;
  const audioOn = draft.mode === "t2v_audio";
  const audioToggleable = draft.mode === "t2v" || draft.mode === "t2v_audio";

  return (
    <Card title="Inspect">
      <div className={styles.stack}>
        <section className={styles.stackTight}>
          <h4>Input preview</h4>
          {media && dataUrl ? (
            <>
              <MediaPreview src={dataUrl} kind={media.kind} label={`Conditioning ${media.kind}: ${media.name}`} />
              {media.kind === "audio" ? <Waveform src={dataUrl} label={`Waveform of ${media.name}`} /> : null}
            </>
          ) : (
            <p className={styles.hint}>No conditioning media attached.</p>
          )}
        </section>

        <fieldset className={styles.group}>
          <legend className={styles.legend}>Preset</legend>
          <div className={styles.row}>
            {PRESET_LIST.map((p) => (
              <PillButton
                key={p.id}
                selected={draft.preset === p.id}
                onClick={() => dispatch({ type: "applyPreset", id: p.id })}
                data-testid={`preset-${p.id}`}
              >
                {p.label}
              </PillButton>
            ))}
          </div>
          {audioToggleable ? (
            <div className={styles.row}>
              <PillButton
                selected={audioOn}
                onClick={() => dispatch({ type: "setMode", mode: audioOn ? "t2v" : "t2v_audio" })}
                data-testid="audio-toggle"
              >
                {audioOn ? "Audio: on" : "Audio: off"}
              </PillButton>
            </div>
          ) : null}
          <p className={styles.hint}>
            {draft.params.height ?? "—"}×{draft.params.width ?? "—"} · frames {draft.params.num_frames ?? "—"} · steps{" "}
            {draft.params.num_inference_steps ?? "—"}
          </p>
        </fieldset>

        <WarningList warnings={advisories} />
      </div>
    </Card>
  );
}
