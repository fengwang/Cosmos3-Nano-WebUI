# Session 2 (UX-S2) - Generation Defaults: Negative-Prompt Preset + 720p Video

Contract: `docs/session_2_contract.yaml`
Risk: medium
Routing: worker_plus_reviewers (worker + sharded review + adversarial verifier)

## Objective

Make good output the zero-configuration default: apply the curated negative
prompt from the model assets as an overridable server-side default, and make
1280×720 the default resolution for video modes at both the API server layer
and the WebUI default preset — leaving text→image defaults and the resolution
picker intact.

## Why This Session Exists

The model ships a curated negative prompt (`assets/negative_prompt.json`) and
generates cleanly at 720p on the quantized path, but the API applies neither
by default: `negative_prompt` has no default and nothing loads the file
(`docs/evidence_map.md` E-04), and the server default resolution is 480 (E-07).
A new user must discover and set both. This session presets them so the
out-of-box result matches the model's intended quality. It is `medium` risk —
the highest-risk of the non-auth sessions — because it adds new server logic
that reads a file from a mount, changes generation defaults, and touches the
GPU-adjacent quantized path (`R-03`..`R-06`).

## In Scope

1. **Negative-prompt default (overridable).** When a generation request omits
   `negative_prompt`, load the curated file and pass it to the engine; a
   user-supplied value overrides it (INV-5). Resolve the file path from the
   configurable model-directory environment variable — **never** a hardcoded
   absolute path (INV-1, `R-03`). If the file is missing/unreadable, log once
   and proceed with no negative prompt (graceful degradation), never crash.
2. **Negative-prompt transport decision.** Confirm, against the vLLM-Omni
   path, whether the backend accepts the structured JSON object directly or a
   serialized string, and wire accordingly (`R-04`, E-05). Record the decision.
3. **WebUI affordance.** Show a "using recommended default" placeholder on the
   negative-prompt field (`webui/components/studio/ComposePanel.tsx:69-71`); a
   typed value still overrides.
4. **720p video default (server).** Make video modes (`t2v`/`i2v`/`t2v_audio`)
   default to 1280×720 when dims are omitted, via mode-aware defaulting in the
   server default path (`api/engines/vllm_omni/client.py:78`,
   `api/orchestrator/gen_worker.py:34`); leave the `t2i` default unchanged
   (`R-06`). Update the `resolution` field description in `api/app/schemas.py:96`.
5. **720p video default (UI).** Make `hi-720` the WebUI default-selected preset
   for video (`webui/lib/studio/presets.ts`, and the draft's initial preset);
   keep `standard-480` and the full resolution picker available (INV-5).
6. **Recommended GPU smoke.** Record a 5090 smoke that the shipped 720p video
   default generates a valid artifact within 32 GB for FP8 **and** NVFP4 at the
   shipped frame count, with the negative-prompt default engaged and the
   guardrails posture noted (`EV-UX-GPU-720-FP8-T2V`, `EV-UX-GPU-720-NVFP4-T2V`,
   `EV-UX-GPU-NEGPROMPT-APPLIED`). Non-blocking; a documented owner-accepted
   deferral is acceptable.

## Out of Scope

- Auth (`UX-S1`), WebUI declutter/media (`UX-S3`), README (`UX-S4`).
- Any change to `t2i` (image) resolution defaults.
- Changing checkpoint revisions or the vLLM-Omni pin.
- Guardrails-on GPU validation, or full validation of any mode beyond the
  recommended 720p video smoke.

## Deliverables

- An overridable server-side negative-prompt default sourced from a
  configurable path with graceful fallback, plus the recorded structured-vs-string
  transport decision.
- Mode-aware 720p video default at server + UI, picker preserved, `t2i`
  unchanged; server default and UI default preset agree for video.
- WebUI "using recommended default" affordance.
- A recorded FP8/NVFP4 720p smoke (or a documented, owner-accepted deferral)
  with the full evidence fields (`docs/eval_seed_cases.md`).

## Deterministic Checks

```bash
rg -n "/data/models" api/            # expect: no hardcoded absolute path in the loader
uv run pytest -m "not gpu"           # incl. new negative-prompt + resolution-default tests
# from webui/
pnpm build && pnpm lint && pnpm typecheck && pnpm test
```

## Exit Criteria

- `GATE-UX-S2-DEFAULTS` passes.
- Negative prompt applies as an overridable default from a configurable path,
  with graceful fallback (`EV-UX-NEGPROMPT-DEFAULT-APPLIED`,
  `EV-UX-NEGPROMPT-NO-ABS-PATH`).
- Video defaults to 1280×720 (server + UI); `t2i` default unchanged; picker
  intact (`EV-UX-RESOLUTION-DEFAULT-VIDEO-720`).
- CPU + WebUI suites green.
- The recommended 720p FP8/NVFP4 smoke is recorded green or carries a
  documented owner-accepted deferral.

## Handoff

Record the negative-prompt transport decision and the measured 720p peak VRAM
(per checkpoint, guardrails posture) into `docs/evidence_map.md`, and note any
residual VRAM caveat (`R-05`) for the README's status callout in `UX-S4`.
