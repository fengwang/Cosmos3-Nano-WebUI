# Session 4 — Hugging Face Checkpoint Verification Note

Date: 2026-07-06
Session: MIG-S4
Gate: `GATE-MIG-S4-HF`

Evidence source: `docs/session_4/probes/verify_hf_checkpoints.py` (torch-free) →
`docs/session_4/probes/evidence.json` (+ `summary.md`). All facts below are reproduced
by re-running the probe. Provenance is scrubbed (R-01): only public repo IDs + revisions
and the `/data/models/<Repo>` mount convention appear; the probe re-runs against public
metadata even without local checkpoints.

## Method

1. Revision resolved two ways and required to agree: `git ls-remote <url> HEAD` and
   `HfApi.model_info().sha`.
2. License + `base_model` + model-card state from `HfApi.model_info().card_data` and the
   public README size.
3. Full public file manifest with per-file size and LFS `sha256` from
   `HfApi.list_repo_files` + `HfApi.get_paths_info(expand=True)`.
4. Local safetensors headers + `quantization_config.json` parsed with the reused
   `tools/checkpoint_prep/safetensors_io.py:parse_header`, **gated** by a `local == public`
   `sha256` cross-check so header/recipe findings describe the *public* artifact.
5. Compatibility evaluated against the imported loader contract
   (`api/engines/diffusers_oracle/loader.py`, `config.py`).

## Verified facts (both public checkpoints)

| Field | `wfen/Cosmos3-Nano-FP8-Blockwise` | `wfen/Cosmos3-Nano-NVFP4-Blockwise` |
|---|---|---|
| Reachable | yes | yes |
| Revision (`ls-remote` == `HfApi.sha`) | `4e181f996abf03f3425298ef692e6e5e56fd46a4` ✓ | `b5c9332efbaefa72c99890b1b1150da12ca9256c` ✓ |
| Model license (`card_data.license`) | `openmdw-1.0` | `openmdw-1.0` |
| Declared `base_model` | `nvidia/Cosmos3-Nano` | `nvidia/Cosmos3-Nano` |
| Model-card state (README bytes) | populated (4,387) | **stub (62)** |
| Public files | 111 | 57 |
| Generation self-contained¹ | yes | yes |
| Transformer shard (probed) | `transformer/diffusion_pytorch_model.safetensors` (19,478,503,280 B) | `transformer/model.safetensors` (14,719,504,288 B) |
| `local == public` sha256 (shard) | **match** (verified-for-public) | **match** (verified-for-public) |
| Header precision (`observe_precision` rule) | fp8 | **unknown** (no `weight_quantizer` keys) |

¹ Both ship `model_index.json`, `config.json`, `generation_config.json`, and the `vae/`,
`text_tokenizer/`, `vision_encoder/`, `sound_tokenizer/`, `scheduler/` component dirs.

## Layout vs the imported diffusers_oracle loader contract

`discover_transformer_dir` (`loader.py:43-49`) requires `*.safetensors` +
`modelopt_state.pt` + `config.json`; `verify_precision`→`precision_from_quant_config`
(`config.py:45`) requires an exact `recipe == "fp8"` or `nvfp4*` from
`quantization_config.json` (else raises).

| Check | FP8 | NVFP4 |
|---|---|---|
| `transformer/` has `modelopt_state.pt` | yes | **no** |
| top-level `quantization_config.json` | yes (sha256 **match**) | **no** |
| `quantization_config.json` `recipe` | `fp8_blockwise_mixed` | (absent) |
| `discover_transformer_dir` result | satisfied | **FileNotFoundError** |
| `verify_precision` result | **ValueError** (recipe ≠ exact `"fp8"`) | **ValueError** ({} recipe) |
| in-process oracle loadable as-is | **no** | **no** |

The NVFP4 transformer instead ships `nvfp4_blockwise_mixed_v1.json` (51,434 B) +
`producer_provenance.json` (396 B) — a vLLM-Omni-native NVFP4 export, not the
modelopt/diffusers export FP8 uses. This is drift **D1** (see `drift_report.md`). The
**default** generation engine is `vllm_omni` (`app/main.py:103`), a separate container
loader (`load_quantized.py`); the in-process `diffusers_oracle`/`diffusers_action` engines
are the affected path. Actual serving compatibility is a `MIG-S6`/`MIG-S8` gate.

## BF16 base model (reasoner + action/forward_dynamics source)

The cards declare `base_model: nvidia/Cosmos3-Nano`. Verified:

| Base repo id | Reachable | Gated | License | `transformer/` | `vision_encoder/` | Card |
|---|---|---|---|---|---|---|
| `nvidia/Cosmos3-Nano` (declared) | **yes** | no | `other` | yes (7 BF16 shards) | yes | populated (43,813 B) |
| `wfen/Cosmos3-Nano` (runtime default dir name) | **not found** | — | — | — | — | — |

The BF16 base the reasoner (`COSMOS3_REASONER_MODEL_DIR`) and the action graft
(`COSMOS3_BASE_ACTION_DIR`) need **is publicly available** at `nvidia/Cosmos3-Nano`
(ungated). This **refutes** the brainstorming premise that reasoning/action were unbacked
(Failure Arbiter FA-1). The only residual limit for those modes is GPU-unverified runtime
(`MIG-S8`). The runtime's default local dir name maps to `nvidia/Cosmos3-Nano`; the
`wfen/Cosmos3-Nano` id must not be used (404) — drift **D2**.

## Cross-check integrity

Both probed transformer shards and the FP8 `quantization_config.json` have local
`sha256 == public LFS sha256` (`match`), so every header/recipe finding above describes the
public artifact, not a stale local build. `git ls-remote` and `HfApi.sha` agree for both
revisions.

## Result

`GATE-MIG-S4-HF` inputs are satisfied: both public revisions recorded and consistent;
license `openmdw-1.0` recorded (separate from repo MIT); full layout + self-containment +
loader-compatibility documented against the imported code; the BF16 base publication is
verified; and every drift (D1–D4) is dispositioned in `drift_report.md` with a routed risk
row. Setup facts flow to `docs/model_setup.md` for `MIG-S6`/`MIG-S7`.
