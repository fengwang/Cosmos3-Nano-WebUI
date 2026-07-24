# P1 Evidence — E-06 Action-Tensor Gap (result: **CONTRADICTED** against the real checkpoint)

Date: 2026-07-24. Method: dependency-free safetensors header read (no torch) +
git inspection + `.env` deployment-config read. Raw facts only; interpretation is
in `decision_record.md` after owner steer.

## Deployment target (what the stack actually serves)
`.env` (repo root, authoritative via `make`'s `--env-file`):
- `COSMOS3_FP8_DIR=/data/models/Cosmos3-Nano-FP8-Blockwise`
- `COSMOS3_NVFP4_DIR=/data/models/Cosmos3-Nano-NVFP4-Blockwise`
- `COSMOS3_GEN_ENGINE=vllm_omni`, `COSMOS3_CHECKPOINT_LABEL=fp8`

So the "real FP8 checkpoint" for E-06 = `/data/models/Cosmos3-Nano-FP8-Blockwise`.

## FP8 checkpoint provenance (git)
- Remote: `git@hf.co:wfen/Cosmos3-Nano-FP8-Blockwise` (the **owner's own** HF repo).
- HEAD: `4e181f9 "lm_head back to bf16"`. History: `2cfbbce initial` →
  `739a1f6 initialize Blockwise FP8 quantization model` → README churn → `4e181f9`.
- Pinned public revision in `docs/model_setup.md` = `9bf5d6ae…12900` — **not present**
  in this repo's history (`git cat-file` fails). The repo was **rebuilt** since the
  blueprint's pin was recorded.

## `action_*` tensor scan (quantized variants + BF16 base)
| Checkpoint | transformer shards | total tensors | `action_*` tensors |
|---|---|---|---|
| FP8 (deployed) | 1 | 1246 | **5** |
| FP8-dist | 1 | 1246 | **5** |
| NVFP4 (deployed) | 1 | 1246 | **5** |
| BF16 base (`/data/models/Cosmos3-Nano`) | 7 | 814 | 5 |

The 5 keys (all checkpoints): `action_modality_embed`, `action_proj_in.{bias,fc}.weight`,
`action_proj_out.{bias,fc}.weight`.

## `action_gen` + quant footprint
- `transformer/config.json`: **`action_gen: true`**, `sound_gen: true`,
  `action_dim: 64`, `num_embodiment_domains: 32`, `model_type: qwen3_vl_text`.
- dtype histogram (FP8 transformer): **1030 BF16 + 216 F8_E4M3**. The `action_*`
  tensors are **BF16** (unquantized), matching E-17 ("small bf16 adapters").
- `weight_quantizer._amax` buffers = **216**. The in-process loader
  (`diffusers_action/loader.py:37`) asserts `GEN_TOWER_QUANTIZED = 505`. **216 ≠ 505**
  → a concrete **drift-D1** signal for the *in-process* graft path (the HEAD commit
  "lm_head back to bf16" reduced the quantized set); the `vllm-omni` container path
  is unaffected (it GPU-verifies `t2i`).

## Action-tensor values (non-zero / real, not placeholders)
- `action_modality_embed` [4096] BF16: first10 non-zero (0.031, 0.026, −0.005, …).
- `action_proj_in.fc.weight` [32, 262144] BF16: first10 non-zero.
- `action_proj_out.fc.weight` [32, 262144] BF16: first10 non-zero.
- `action_proj_out.bias.weight` [32, 64] BF16: zero (expected — bias init).

## `-dist` prior-art (owner's self-contained build)
`self_contained_provenance.json`: built by **`checkpoint_prep.copy_shared (P6-S6)`**
on 2026-07-06, sweeping 63 files from the BF16 base into a `reasoner/` subdir (full
7-shard BF16 transformer ~30 GiB, vision_encoder, tokenizers) + shared
`vae/`/`sound_tokenizer/`. So `-dist` = quantized generation checkpoint **+ bundled
full BF16 reasoner** = *self-contained*, but **not zero-BF16 for reasoning**.

## Pinned public revision `9bf5d6ae` — verified on HF (header range-read, no full download)
The owner asked to also verify the blueprint's cited PUBLIC pin. Via the HF API +
an HTTP range read (no 19 GB download):
- API tree at `9bf5d6ae` → `transformer/` = `config.json` (1383 B),
  `diffusion_pytorch_model.safetensors` (**19,478,503,280 B**, single LFS file),
  `modelopt_state.pt` (670 KB); HTTP 200 → the pin **exists** on HF.
- `transformer/config.json` @ `9bf5d6ae`: **`action_gen: true`**.
- safetensors header (range-read first 2 MB, HTTP 206; declared header N=146792 B):
  **total_tensors=1246, `action_*`=5** (same keys), dtype 1030 BF16 + 216 F8_E4M3,
  `_amax` buffers=216.
- ⇒ the `action_*` adapters are present **at the blueprint's own pinned public
  revision**. The on-disk `4e181f9` (18.58 GB) differs only by the "lm_head back to
  bf16" re-quant; the action content is identical.
- The code constant `GEN_TOWER_QUANTIZED=505` matches **neither** revision (both
  216) → the in-process-loader D1 precision-check mismatch is **revision-independent**.

## Raw verdict
1. **E-06 is contradicted at BOTH the pinned public revision (`9bf5d6ae`, verified
   on HF) AND the on-disk checkpoint (`4e181f9`)**: the quantized FP8 (and NVFP4,
   and dist) checkpoints **already ship the BF16 `action_*` adapters** with
   `action_gen: true` and real values. The "action-tensor gap" does **not** exist on
   the checkpoint at any revision; E-06 was inferred from the loader code, never
   validated against the checkpoint bytes (which is exactly what AM-S1 exists to do).
2. **Nuance — code vs checkpoint**: `diffusers_action/loader.py` still *grafts*
   `action_*` from the BF16 base (`COSMOS3_BASE_ACTION_DIR`) — the serving **code**
   has not moved to the checkpoint's own tensors. So "zero-BF16 action" shifts from
   a *checkpoint-packaging* problem (R-01, ~solved) to a *serving-path* question.
3. **D1 signal**: the in-process loader's `expected_quantized=505` won't match the
   current 216 → the `(c)` in-process load likely fails its precision check (P6).
4. **Residual (for AM-S3, not this spike)**: verify the checkpoint action-tensor
   *values* match the base's trained adapters bit-for-bit.

## Per-design gate (design.md P1)
Design's gate: "E-06 confirmed **iff** A (pinned FP8 transformer) has NO `action_`
AND B (BF16 base) has them." Actual: A has **5** → the 'confirmed' gate **fails** →
E-06 is **refuted**. The rubric had no "gap already closed" branch, so the packaging
`GO` consequence (§P2) is an evidence-driven *update*, not a frozen rubric branch.

## Scope of value-sampling
Non-zero *values* were byte-sampled on the **deployed FP8** transformer only. The
pinned public `9bf5d6ae` and NVFP4 were confirmed at the **header level** (keys +
dtype + shape) — a 2 MB range-read cannot see weight bytes — i.e. presence, not
values.

## Receipts (commands + trimmed raw output)
```
$ git -C /data/models/Cosmos3-Nano-FP8-Blockwise rev-parse HEAD
4e181f996abf03f3425298ef692e6e5e56fd46a4     # "lm_head back to bf16"; pinned 9bf5d6ae NOT in history
# dependency-free safetensors header scan (struct+json, no torch):
PINNED-FP8 transformer: shards=1 total_tensors=1246 action_tensors=5
    + action_modality_embed, action_proj_in.{bias,fc}.weight, action_proj_out.{bias,fc}.weight
BF16-BASE  transformer: shards=7 total_tensors=814  action_tensors=5
# non-zero value sample (deployed FP8):
action_modality_embed      BF16 [4096]      first10=[0.0315,0.0263,-0.0053,...]  nonzero=10/10
action_proj_out.fc.weight  BF16 [32,262144] first10=[-0.0105,0.0116,0.0028,...] nonzero=10/10
action_proj_out.bias.weight BF16 [32,64]    first10=[0.0,...]                    nonzero=0/10 (bias init)
# HF pinned-public 9bf5d6ae (HTTP 206 range-read, header only):
total_tensors=1246 action_tensors=5  dtype={BF16:1030, F8_E4M3:216}  _amax buffers=216
```
