# Session 4 — Checkpoint Drift Report

Date: 2026-07-06
Session: MIG-S4

Drift between the public Hugging Face artifacts and the imported runtime's assumptions.
Each row has an owner disposition and a routed risk row; none is left open without an owner
session. Evidence: `docs/session_4/probes/evidence.json` (`local == public` sha256 verified
for the probed shards + FP8 quant config, so these describe the public artifacts).

## D1 — In-process diffusers_oracle cannot load+verify the current public checkpoints (HIGH)

- **Evidence.**
  - FP8: `discover_transformer_dir` is satisfied (`modelopt_state.pt` present), but the public
    `quantization_config.json` `recipe` is `fp8_blockwise_mixed` (quant-config sha256 `match`),
    while `config.py:45` requires the exact string `recipe == "fp8"` → `verify_precision` raises
    `ValueError`.
  - NVFP4: `transformer/` has no `modelopt_state.pt` and there is no top-level
    `quantization_config.json` → `discover_transformer_dir` (`loader.py:33-50`) raises
    `FileNotFoundError`; the shard header carries no `weight_quantizer` keys
    (`observe_precision` → unknown). NVFP4 ships a vLLM-Omni-native export
    (`transformer/nvfp4_blockwise_mixed_v1.json`, `producer_provenance.json`).
- **Loader impact.** The imported *in-process* `diffusers_oracle`/`diffusers_action` engines
  cannot load+verify **either** current public checkpoint as-is. The **default** generation
  engine is `vllm_omni` (`app/main.py:103`), a separate container loader (`load_quantized.py`)
  not exercised by this docs-only probe.
- **Disposition.** Session 4 is docs-only and MUST NOT edit engine code. Recorded; the default
  `vllm_omni` serving path MUST be validated on GPU before Docker/README claim generation. A
  code follow-up (accept `fp8_blockwise_mixed`; make NVFP4 loadable in-process or document
  in-process as FP8-modelopt-only) is **out of `MIG-S4` scope**.
- **Owner / routed risk.** `MIG-S6` (serving wiring) + `MIG-S8` (GPU validation); risk **R-03**.

## D2 — BF16 base is public but under a different repo id than the runtime default (LOW)

- **Evidence.** Checkpoint cards declare `base_model: nvidia/Cosmos3-Nano`, which is
  **reachable, ungated, public** (license `other`, has `transformer/` + `vision_encoder/`).
  The runtime's default base dir name is `Cosmos3-Nano`; the id `wfen/Cosmos3-Nano` is
  **not found** (404).
- **Impact.** Reasoning (`COSMOS3_REASONER_MODEL_DIR`) and action/`forward_dynamics`
  (`COSMOS3_BASE_ACTION_DIR`) are **publicly backed** by `nvidia/Cosmos3-Nano`; the only
  residual limit is GPU-unverified runtime (`MIG-S8`). This **corrects** the pre-verification
  premise that these modes were unbacked (Failure Arbiter FA-1).
- **Disposition.** `docs/model_setup.md` records the correct base id and revision and warns
  against `wfen/Cosmos3-Nano`. No code change needed (the default local dir name is operator
  mapping, not a repo id).
- **Owner / routed risk.** `MIG-S7` (README uses the correct id); risk **R-03**.

## D3 — Public repos ship dev-scratch / provenance / loader-script files (LOW)

- **Evidence (existence only; contents not read — R-01).**
  - `wfen/Cosmos3-Nano-FP8-Blockwise`: `_s2_postfix.md`, `_s2_rerun.md`, `_s2_verify.md`,
    `load_checkpoint.py`, `load_quantized.py`.
  - `wfen/Cosmos3-Nano-NVFP4-Blockwise`: `transformer/producer_provenance.json`.
- **Impact.** External-repo hygiene: dev-process scratch files and a provenance file may carry
  build context; asymmetric loader scripts (FP8 only) may confuse users.
- **Disposition.** Recommend an out-of-band HF-side cleanup by the model owner (remove
  `_s2_*` scratch; review `producer_provenance.json` for any private build provenance before
  it stays public; decide whether the loader scripts belong). This repo does not (and cannot)
  edit the external HF repos. Contents are **not** reproduced here.
- **Owner / routed risk.** Owner / external follow-up; risk **R-01** (public-surface hygiene),
  re-scan at `MIG-S8`.

## D4 — NVFP4 model card is a 62-byte stub (MEDIUM)

- **Evidence.** NVFP4 `README.md` = 62 bytes (frontmatter-only stub); FP8 card = 4,387 bytes
  (populated); base card = 43,813 bytes. S1 had recorded the NVFP4 card as "empty" — it is now
  a stub, still not a usable model card.
- **Impact.** Public NVFP4 users lack setup context on the model page itself (R-04).
- **Disposition.** Compensated in-repo by `docs/model_setup.md` (revision, license, env,
  mount, matrix). Populating the HF model card is an external follow-up (HF write — out of
  this repo's scope).
- **Owner / routed risk.** `MIG-S7` (in-repo docs) + external card follow-up; risk **R-04**.

## Summary

| ID | Severity | Disposition | Owner session | Risk |
|---|---|---|---|---|
| D1 | High | Documented; default `vllm_omni` path to validate; in-process fix out of scope | MIG-S6, MIG-S8 | R-03 |
| D2 | Low | Correct base id recorded in `model_setup.md` | MIG-S7 | R-03 |
| D3 | Low | Recommend external HF-side cleanup; contents not read | Owner / external | R-01 |
| D4 | Medium | Compensated in `model_setup.md`; HF card follow-up | MIG-S7 / external | R-04 |

No drift blocks this documentation gate; all are dispositioned before Docker (`MIG-S6`) or
README (`MIG-S7`) depend on the checkpoints. The one release-relevant compatibility risk (D1)
is routed to the GPU/serving gates with explicit evidence.
