# P1 — Owner video-mode runs (t2v / i2v / t2v_audio) — recorded end-to-end run + quality PASS

Date: 2026-07-26 · Session: AM-S6 · Operator/authority: **Feng (owner)** · Hardware: RTX 5090 (sm_120).

This note records the **owner-operated end-to-end runs** of the three Studio video generation modes,
captured to satisfy INV-6 limb (i) — *a recorded end-to-end run on the RTX 5090* — for those modes.
It complements the owner's quality verdict (limb ii). It is the analogue, for the video modes, of the
owner quality attestations in `docs/session_2/evidence/P2` (reasoning) and the AM-S3/S5 audits (action).

## Recorded run (owner report, confirmed 2026-07-26)

Via the **WebUI Studio** on **both the FP8 and NVFP4** stacks, the owner ran:

| Mode | FP8 | NVFP4 | Observed |
|---|---|---|---|
| **text→video** (`t2v`) | ran | ran | valid, coherent, on-prompt clip at default **1280×720 (~49 frames)**, played back |
| **image→video** (`i2v`) | ran | ran | start frame animated into a valid ~720p clip, played back |
| **text→video+audio** (`t2v_audio`) | ran | ran | ~720p clip with a matching **audio track present**, played back |

All runs produced a valid clip that played back in the Studio; **no errors**. Output judged **high
quality** across all three modes on both formats.

## INV-6 mapping (both limbs met → GPU-verified)

- **(i) Recorded end-to-end run on the RTX 5090** — ✓ this note (owner-operated, both formats, all three
  video modes, valid clips produced and played back).
- **(ii) Owner recorded manual quality PASS** — ✓ "all works very well, high quality" (Feng, 2026-07-26).
- ⇒ **`t2v` / `i2v` / `t2v_audio` are GPU-verified on FP8 and NVFP4** (INV-6 satisfied per mode/format);
  default-on holds (INV-7). This is the AM-S6 owner-authorized amendment to the AM-S5 matrix, which had
  represented Studio by `t2i` only and listed the video modes as smoke-only.

## Honesty / scope notes

- This is an **owner-operated** run recorded from the owner's direct report — the owner is both the
  operator and the quality-gate authority (PRD Decision 6). It is **not** an agent-captured GPU probe with
  byte-level artifact metadata (as the t2i/reasoning/action P-files are); the recorded facts are the
  formats exercised, that valid clips were produced and played back, that audio was present for
  `t2v_audio`, and the quality verdict — no synthetic detail is added beyond what the owner confirmed.
- **Scope is strictly** the three video modes × two formats above. Nothing else in the per-mode matrix is
  re-touched by this record; `t2i`, reasoning, and action retain their own AM-S2..S5 evidence.
- The served path is the quantized `vllm-omni` container (zero BF16), the same path GPU-verified for
  `t2i` under `GPU-S3`; video defaults are the shipped 1280×720 / 49-frame settings documented in the
  README and `docs/model_setup.md`.
