# Public Model Setup Contract

Status: authoritative setup contract (MIG-S4). Source of truth for `MIG-S6` (Docker/Compose)
and `MIG-S7` (README). This file records the checkpoint facts and configuration surface; it is
**not** the public README — polished quickstart/marketing prose is `MIG-S7`, and Docker/Compose
wiring is `MIG-S6`. Evidence: `docs/archive/phase-1/session_4/hf_verification.md` +
`docs/archive/phase-1/session_4/probes/evidence.json`. Verified 2026-07-06.

## 1. Checkpoints (public Hugging Face repos, pinned)

| Purpose | Repo id | Pinned revision | Model license |
|---|---|---|---|
| Quantized generation (FP8) | `wfen/Cosmos3-Nano-FP8-Blockwise` | `9bf5d6ae164688487bdb71947ccc6ebe70d12900` | `openmdw-1.0` |
| Quantized generation (NVFP4) | `wfen/Cosmos3-Nano-NVFP4-Blockwise` | `5514c42b9759739f545e0d0dee453db8d8525fbc` | `openmdw-1.0` |
| BF16 base (reasoner + action graft) | `nvidia/Cosmos3-Nano` | `fea6e03ac3d7884b4105ed8ee79fc480fca70965` | `other` |

Consumers SHOULD pin the revision (not the mutable `main`). Do **not** use
`wfen/Cosmos3-Nano` for the base — that id does not exist (404); the base is
`nvidia/Cosmos3-Nano` (public, ungated).

## 2. Licensing (keep separate — INV-7)

- **Repository code:** MIT (this WebUI/API repo).
- **Model weights:** `openmdw-1.0` for the FP8/NVFP4 checkpoints; `other` for the
  `nvidia/Cosmos3-Nano` base. These are the model owners' licenses, **distinct** from the
  repo's MIT license. README (`MIG-S7`) MUST present them separately and MUST NOT describe
  the weights as MIT.

## 3. Weights are external (INV-2)

Weights are downloaded or mounted by the operator from the public repos above. No weights are
committed to Git or baked into Docker images. Each checkpoint is **self-contained** for the
diffusers generation pipeline (ships `model_index.json`, `config.json`, `generation_config.json`,
and `vae/`, `text_tokenizer/`, `vision_encoder/`, `sound_tokenizer/`, `scheduler/`).

## 4. Environment variables (checkpoint-relevant)

All defaults use the documented `/data/models/<Repo>` mount convention and are
operator-configurable (INV-4). Citations are `file:line` in the imported source.

| Variable | Purpose | Default | Source |
|---|---|---|---|
| `COSMOS3_MODEL_DIR` | Quantized generation checkpoint root | `/data/models/Cosmos3-Nano-NVFP4-Blockwise` (oracle); `/data/models/Cosmos3-Nano-FP8-Blockwise` (action, orchestrator)¹ | `diffusers_oracle/config.py:15`; `diffusers_action/loader.py:56`; `app/main.py:152` |
| `COSMOS3_CHECKPOINT_LABEL` | Deployment's checkpoint label, `fp8` \| `nvfp4` | `fp8` | `engines/vllm_omni/endpoints.py:21,27` |
| `COSMOS3_REASONER_MODEL_DIR` | BF16 base — reasoner understanding tower | `/data/models/Cosmos3-Nano` (→ `nvidia/Cosmos3-Nano`) | `engines/vllm/loader.py:30` |
| `COSMOS3_BASE_ACTION_DIR` | BF16 base transformer — action-adapter graft | `/data/models/Cosmos3-Nano/transformer` | `diffusers_action/loader.py:36` |
| `COSMOS3_GEN_ENGINE` | Generation engine selector | `vllm_omni` | `app/main.py:103` |
| `COSMOS3_VLLM_OMNI_URL` / `COSMOS3_GEN_CONTAINER` | vLLM-Omni generation endpoint | container-internal defaults | `engines/vllm_omni/endpoints.py:48-49` |
| `COSMOS3_DEVICE` | Compute device | `cuda` | `diffusers_oracle/config.py:30` and others |

¹ The imported source has an **internal default inconsistency**: the in-process oracle
defaults `COSMOS3_MODEL_DIR` to NVFP4 while the action engine and orchestrator default it to
FP8. Operators SHOULD set it explicitly. (Not fixed here — code is outside the `MIG-S4` blast
radius; noted for `MIG-S6`.)

## 5. Mount layout (example)

```
/data/models/                         # COSMOS3 mount root (convention; any path via env)
├── Cosmos3-Nano-FP8-Blockwise/       # from wfen/Cosmos3-Nano-FP8-Blockwise
├── Cosmos3-Nano-NVFP4-Blockwise/     # from wfen/Cosmos3-Nano-NVFP4-Blockwise
└── Cosmos3-Nano/                     # from nvidia/Cosmos3-Nano (BF16 base)
```

A single-checkpoint generation deployment serves exactly one of FP8 **xor** NVFP4
(`COSMOS3_CHECKPOINT_LABEL`); reasoning/action additionally need the BF16 base.

## 6. Per-mode compatibility matrix (verified)

All modes' weights are **publicly obtainable**. The residual limits are (a) GPU-unverified
runtime — the blanket `MIG-S8` gate (INV-8) — and (b) drift **D1**: the imported *in-process*
`diffusers_oracle`/`diffusers_action` engines cannot load+verify the *current* public
checkpoints as-is. The **default** generation engine is `vllm_omni` (a separate container
loader), whose real compatibility is a `MIG-S6`/`MIG-S8` gate.

| Mode | Public weights | Default serving path | In-process oracle path | Residual limit |
|---|---|---|---|---|
| `t2i` | FP8 **or** NVFP4 quantized checkpoint | `vllm_omni` container (`load_quantized.py`) | not loadable as-is (D1) | **T2I-verified (`GPU-S3`, 2026-07-09):** fresh `hf download` at the `GPU-S2` revisions, through the unmodified `GPU-S1` image, direct **and** full-stack, no manual workaround; D1 remains for the in-process path only |
| `t2v`, `t2v_audio`, `i2v` | FP8 **or** NVFP4 quantized checkpoint | `vllm_omni` container (`load_quantized.py`) — verify `S6`/`S8` | not loadable as-is (D1) | GPU-unverified (`S8`); D1 for in-process path. (A best-effort NVFP4 `t2v` smoke passed under `GPU-S3` — see `docs/evidence_map.md` — but `t2v_audio`/`i2v` and any full validation of `t2v` remain unrun; this residual limit is otherwise unchanged.) |
| reasoning | base `nvidia/Cosmos3-Nano` (BF16) | separate vLLM reasoner instance | n/a | GPU-unverified (`S8`) |
| action / `forward_dynamics` | FP8 checkpoint **+** base `nvidia/Cosmos3-Nano` (BF16 action tensors) | in-process `diffusers_action` graft | FP8 verify blocked (D1) | GPU-unverified (`S8`); D1 |

No mode is beta-limited for missing weights (the base `nvidia/Cosmos3-Nano` is public — this
corrects the pre-verification premise; see Failure Arbiter FA-1).

## 7. Drift caveats (see `docs/archive/phase-1/session_4/drift_report.md`)

- **D1 (high) — characterized 2026-07-08:** the in-process `diffusers_oracle` cannot load the
  current public FP8 (recipe `fp8_blockwise_mixed` ≠ exact `"fp8"`) or NVFP4 (no
  `modelopt_state.pt` / `quantization_config.json`; vLLM-Omni-native export) checkpoints. **The
  default `vllm_omni` container path DOES load both** (FP8 `W8A16`, NVFP4 `W4A16`) and generates
  **T2I** on an RTX 5090 — the stale top-level `model.safetensors.index.json` is now removed at
  the source (`GPU-S2`, see §9), so no manual removal step is needed at the revisions in §1. So
  D1 affects the in-process oracle only; the packaging bug (stale index, R-03) is closed. T2I
  verified; `t2v`/`t2v_audio`/`i2v`/`forward_dynamics`/`reasoning` + 720p video not yet.
  **`GPU-S3` (2026-07-09) additionally closes the joint gap** these two facts left open on
  their own: a fresh `hf download` at the revisions in §1, through the *unmodified*, from-source
  `GPU-S1` image (not a prebuilt proxy), generates T2I for both FP8 and NVFP4 with no manual
  workaround — direct and full-stack. See `docs/evidence_map.md`.
- **D2 (low):** use base id `nvidia/Cosmos3-Nano` (public); `wfen/Cosmos3-Nano` 404s.
- **D3 (low):** the public FP8 repo ships dev-scratch (`_s2_*.md`) + loader scripts and NVFP4
  ships `producer_provenance.json`; recommend HF-side cleanup (external follow-up).
- **D4 (medium):** the NVFP4 model card is a 62-byte stub — this repo's setup docs compensate
  (R-04); populating the HF card is an external follow-up.

## 8. Operator setup (minimal — full quickstart is `MIG-S7`)

1. Install `huggingface_hub`; authentication is not required (all three repos are public,
   ungated).
2. Download or mount the checkpoint(s) you serve into the mount root, e.g. FP8 generation:
   `hf download wfen/Cosmos3-Nano-FP8-Blockwise --revision 9bf5d6ae164688487bdb71947ccc6ebe70d12900 --local-dir /path/to/Cosmos3-Nano-FP8-Blockwise`.
   A plain `git clone` resolves cleanly too as of this revision (§9).
3. For reasoning or action/`forward_dynamics`, also fetch the base
   `nvidia/Cosmos3-Nano` and set `COSMOS3_REASONER_MODEL_DIR` / `COSMOS3_BASE_ACTION_DIR`.
4. Point `COSMOS3_MODEL_DIR` (and `COSMOS3_CHECKPOINT_LABEL`) at the served checkpoint.
5. GPU inference is a manual release gate (`MIG-S8`). **T2I is now GPU-verified (2026-07-08,
   FP8 + NVFP4, RTX 5090)**, and as of **`GPU-S3` (2026-07-09)** this holds for a fresh
   checkpoint download through the unmodified, from-source `GPU-S1` image with no manual
   workaround, direct and full-stack; other modes and 720p video remain manual gates.

## 9. Known packaging workarounds — fixed at the source (`GPU-S2`, 2026-07-09)

Loading the public `wfen/*` checkpoints in the `vllm_omni` container previously needed two
operator workarounds. **Both are fixed at the source as of the revisions in §1** — a plain
`git clone` or `hf download` now resolves every file to real content with no manual step:

1. ~~Prefer `hf download` over `git clone`.~~ Both repos' `.gitattributes` forced every small
   config/tokenizer/script file into LFS regardless of size, so a `git clone` left them as
   unresolved LFS pointers. Fixed by scoping LFS to files over 10 MB or non-plain-text
   (large weights only); small files are now regular Git blobs that resolve on any clone.
2. ~~Remove the stale weight index.~~ Each checkpoint shipped a top-level
   `model.safetensors.index.json` referencing non-existent sharded files
   (`transformer/diffusion_pytorch_model-0000N-of-00007.safetensors`); the real transformer
   weight is a single consolidated `transformer/{diffusion_pytorch_model,model}.safetensors`.
   The stale index is now removed from both repos at the source.

An operator pinned to a revision older than §1's (not recommended) still needs the manual
`mv <dir>/model.safetensors.index.json <dir>/model.safetensors.index.json.bak` workaround and
should prefer `hf download` over `git clone` for the reasons above.

Serve (fork's OpenAI-compatible entrypoint, per `vllm-omni` `recipes/cosmos3/Cosmos3-Nano.md`):

```
vllm serve <checkpoint-dir> --omni --host 0.0.0.0 --port 8000 --init-timeout 1800 [--no-guardrails]
```

`--no-guardrails` is for a quick local run; guardrails-on needs the gated
`nvidia/Cosmos-1.0-Guardrail` model + `HF_TOKEN`. The api validates T2I dimensions against
`{256, 480, 640, 720, 960, 1280}`.
