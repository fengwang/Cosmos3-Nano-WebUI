# Eval Seed Cases - All Modes, GPU-Verified, Default-On

Date: 2026-07-24

These cases seed the checks for `AM-S1`..`AM-S6`. Unlike phase-4, this phase
**requires GPU smokes**: enabling a mode means running it on the RTX 5090. Each
enablement session therefore has (i) deterministic host-runnable checks, (ii) a
blocking GPU smoke, and (iii) — for reasoning/action — the owner's manual quality
gate. GPU inference is no longer only the standing `MIG-S8` manual gate; this
phase promotes specific modes through explicit, recorded GPU verification.

## Fixed references

- Public checkpoints + the `vLLM-Omni` pin: `docs/model_setup.md` §1/§9,
  `.env.example`. `AM-S3`/`AM-S5` may add a **new** action-bundled checkpoint
  revision; if so it is pinned immutably and recorded there (NFR-5). Existing
  `t2i` revisions are re-verified, never silently replaced.
- Guardrails-off (E-15), no application auth, loopback default, idle keep-warm
  1800 s (E-16): unchanged.

## Deterministic checks (host-runnable)

| ID | Purpose | Inputs | Expected properties | Gate |
|---|---|---|---|---|
| EV-AM-CPU-SUITE-GREEN | The CPU suite stays green after each code session. | `uv run pytest -m "not gpu"`. | All green; any test that hard-codes the old reasoning/action wiring is updated (not reverted) to the new default (R-14). | AM-S2..S5 |
| EV-AM-SPIKE-DECISION-RECORDED | The spike's outcome is captured as a decision, not a vibe. | The `AM-S1` working doc + `docs/evidence_map.md` update. | A per-mode `(a)`/`(c)` decision for reasoning and action; a zero-BF16 action packaging decision; the action-tensor gap (E-06) confirmed against the real checkpoint; owner sign-off recorded. | AM-S1 |
| EV-AM-ZERO-BF16-WIRING | The default stacks require no BF16 base, no overlay, no `WITH_REASONING`. | `docker compose -f deploy/docker-compose.fp8.yml config` (and the nvfp4 file); the default `api` build args. | No bind-mount of a BF16 base in the rendered config; no `docker-compose.reasoning.yml` needed for all-modes; the default `api` image builds without `WITH_REASONING=1`. | AM-S4 (FP8), AM-S5 (NVFP4) |
| EV-AM-NO-OVERLAY-DEFAULT | `make up-fp8` alone is all-modes; the overlay is gone or clearly optional-legacy. | `rg -n "up-fp8-reasoning|docker-compose.reasoning" Makefile deploy .env.example`; inspect `Makefile` targets. | A single `make up-fp8` brings up all three modes; no separate all-modes overlay step remains as the documented path. | AM-S4 |
| EV-AM-CHECKPOINT-INTEGRITY | A re-exported action-bundled checkpoint is valid and pinned, not corrupt or in-place. | `tools/checkpoint_prep` `integrity_probe` on the new checkpoint; `docs/model_setup.md` diff. | Integrity probe passes; `action_*` tensors present; a **new** immutable revision is pinned and recorded; the public `main`/prior revision is untouched (R-10). | AM-S3 |
| EV-AM-SCHEMA-STABLE | The public API schema shape does not drift unless authorized. | `git diff schemas/openapi.json`; the schema-sync gate. | No shape change unless the session contract authorized it and re-ran the sync gate (INV-8). | AM-S2..S5 |
| EV-AM-README-VERIFIED-SUBSET | No mode is claimed verified beyond what passed the owner gate. | Compare every "GPU-verified" claim in `README.md` against the set of modes/formats with a recorded run + owner PASS. | The README's verified set is a subset of the evidence-map verified set, per format and per mode; no hook/benefit/example implies otherwise (INV-6). | AM-S6 |
| EV-AM-WALKTHROUGH-STRUCTURE | The walkthrough teaches each mode by example with fillable placeholders and commits no binary. | Structure asserts over `docs/walkthrough.md`: a section per mode with an example input, an expected-output description, and an `![...](docs/images/…)` placeholder; `git status` shows no image binary added. | Each mode present with input + expected output + image placeholder; every image link points under `docs/images/`; no committed image/media binary (NFR-1). | AM-S6 |
| EV-AM-DOCS-LINKS-RESOLVE | Internal links resolve and the license discrepancy is reconciled. | Relative-link + anchor resolver over `README.md`, `docs/walkthrough.md`, and `docs/model_setup.md`; check the BF16 base license line. | Every link/anchor resolves; the BF16-base license (E-14) is stated once, consistently, reconciled against the HF source. | AM-S6 |

## GPU smokes (blocking this phase)

Each records the standard evidence fields (below). Fresh checkpoint download at
the pinned revision, through the unmodified from-source image, no manual workaround
(the `GPU-S3` bar).

| ID | Purpose | Expected result | Gate |
|---|---|---|---|
| GPU-AM-T2I-NOREGRESS | `t2i` still generates end to end after the session's serving-path change. | A valid image for FP8 (and NVFP4 from `AM-S5`), direct **and** full-stack; matches the `GPU-S3` baseline; no regression (INV-2). | AM-S2..S5 |
| GPU-AM-REASON-FP8 | `/v1/reason` streams a coherent completion off the **quantized-only** FP8 checkpoint (no BF16). | A streamed chat completion from the WebUI Reasoning tab and the API; no BF16 base mounted. | AM-S2 |
| GPU-AM-ACTION-FP8 | `/v1/action/{policy,forward_dynamics,inverse_dynamics}` produces a trajectory/artifact off a **quantized-only** FP8 checkpoint. | A valid trajectory rendered in the Action tab's 3D/2D viewer for the v1-scope embodiments (agibotworld 29-D; av 9-D). | AM-S3 |
| GPU-AM-ALLMODES-FP8 | A single `make up-fp8` serves all three modes with correct on-demand residency swaps. | Studio, Reasoning, and Action each work in one deployment; a different-mode request preempts the resident plane without OOM (INV-5); `t2i` non-regressed. | AM-S4 |
| GPU-AM-ALLMODES-NVFP4 | The all-modes design works on NVFP4, per mode. | Each mode passes on NVFP4 (owner quality PASS) or its limitation is a recorded owner decision (INV-7); `t2i` (NVFP4) non-regressed. | AM-S5 |

## Owner quality gates (human decision)

| ID | Purpose | Inputs | Pass condition | Gate |
|---|---|---|---|---|
| OWNER-AM-REASON-QUALITY | The owner rules on reasoning output quality (S-B). | The owner runs several custom example prompts against the running container. | Owner records **PASS** (with the prompts used) before reasoning is promoted to "verified"/default-on; else an explicit owner decision (accept-lower / use `(c)` / document limitation). | AM-S2 (FP8), AM-S5 (NVFP4) |
| OWNER-AM-ACTION-QUALITY | The owner rules on action output quality. | The owner runs the v1-scope action demos/prompts and inspects trajectories. | Owner records **PASS** before action is promoted; else an explicit owner decision. | AM-S3 (FP8), AM-S5 (NVFP4) |

## Adversarial cases (seed the verifiers)

- A mode is marked "GPU-verified" from a single successful run with **no** owner
  quality verdict recorded (INV-6 breach).
- A BF16 base bind-mount or `WITH_REASONING=1` sneaks back into the default stack,
  so "zero-BF16" is only half-true (INV-4 breach; caught by `EV-AM-ZERO-BF16-WIRING`).
- Reasoning/action is added and `t2i` silently regresses because no `t2i` smoke was
  re-run (INV-2 breach; caught by `GPU-AM-T2I-NOREGRESS`).
- The action checkpoint is mutated **in place** or `main` is repointed, so a fresh
  download no longer matches the pinned revision (R-10; caught by
  `EV-AM-CHECKPOINT-INTEGRITY`).
- `docs/walkthrough.md` states an "expected output" for a mode that never ran on
  GPU, or embeds a committed screenshot binary (R-13; caught by
  `EV-AM-WALKTHROUGH-STRUCTURE` + the honesty pass).
- A session routes `t2v` through `diffusers` to "unify engines" (INV-3 breach).
- NVFP4 fails to serve reasoning/action and the README nonetheless claims NVFP4
  all-modes (INV-7 breach; caught by `EV-AM-README-VERIFIED-SUBSET`).

## Evidence fields (per GPU smoke)

Record for each GPU smoke, per the archived `docs/archive/phase-3/eval_seed_cases.md`
template: hardware (RTX 5090, sm_120), driver/CUDA, checkpoint repo id + pinned
revision, deployment stack (fp8/nvfp4) and whether any BF16 was mounted, request
shape (mode + params), peak VRAM (nvidia-smi), guardrails posture (`--no-guardrails`),
artifact metadata (dimensions/frames/trajectory dims), result (pass/fail), and — for
reasoning/action — the **owner's quality verdict** with the example prompts used.

*(Execution harvests are appended by each session as it closes, following the
phase-4 pattern.)*

## AM-S1 execution harvest (2026-07-24)

**Checks satisfied**
- **EV-AM-SPIKE-DECISION-RECORDED** — SATISFIED. `docs/session_1/decision_record.md`
  records per-mode `(a)`/`(c)` for reasoning (`c`) and action (`a`-target/`c`-fallback),
  the zero-BF16 action packaging decision (GO/already-done), the residency implication
  (Studio+Action merge candidate; reasoning swaps), and E-06 confirmed **against the
  real checkpoint** (refuted). Owner sign-off: decision_record §8.
- **EV-AM-CPU-SUITE-GREEN** — SATISFIED. `uv run pytest -m "not gpu"` = 523 passed at
  session start, re-run at close, and again by the independent adversarial verifier.

**New seeds harvested (issues the spike caught — seed the verifiers)**
- **EV-AM-PREMISE-VS-ARTIFACT** — A blueprint premise marked *High confidence*
  (E-06, "quantized checkpoint ships without action tensors") was derived from the
  **code** (the loader grafts from the BF16 base), never validated against the
  **artifact**. AM-S1's byte-level inspection of the real checkpoint **refuted** it
  (adapters present at both the pinned public and deployed revisions). *Test the
  agent:* when a contract cites a checkpoint/binary fact, does it inspect the real
  artifact, or trust a code-derived inference? A "gap confirmed" claim without an
  artifact scan is a miss.
- **EV-AM-CHAT-IS-IMAGE** — `vllm-omni` `/v1/chat/completions` returns HTTP 200 with
  an **image** for a text prompt. *Test the agent:* does it record "reasoning works"
  from HTTP 200 / a loaded server (feasibility↔quality + modality conflation), or
  does it check that the *content* is coherent text? The correct verdict is "chat is
  image-gen; reasoning not served."

## AM-S2 execution harvest (2026-07-25)

**Checks satisfied**
- **GPU-AM-REASON-FP8** — SATISFIED (`docs/session_2/evidence/P2`): coherent text + streaming SSE
  off the quantized-only FP8 checkpoint, no BF16, from the reproducible `deploy/vllm-reasoner`
  image. **OWNER-AM-REASON-QUALITY (FP8)** = PASS (owner, 2026-07-25).
- **GPU-AM-T2I-NOREGRESS** — SATISFIED (`P3`): valid 480×480 PNG off the unchanged omni image.
- **EV-AM-CPU-SUITE-GREEN**, **EV-AM-SCHEMA-STABLE** — SATISFIED (CPU suite green; `openapi.json`
  unchanged). Reasoning-path portion of **EV-AM-ZERO-BF16-WIRING** met (`docker compose -f
  deploy/docker-compose.fp8.yml config` shows no BF16 mount); the full default-on gate stays AM-S4.

**New seeds harvested (issues AM-S2 caught — seed the verifiers)**
- **EV-AM-QUANT-SIDECAR-NOT-AUTODETECTED** — The FP8-blockwise quant lives in a **side**
  `quantization_config.json` + `transformer/modelopt_state.pt` (not the HF-standard
  `hf_quant_config.json` / a `config.json` `quantization_config` key). So stock vLLM auto-detect
  loads it as BF16 → `KeyError: ...weight_quantizer._amax`, and `--quantization modelopt` fails with
  "Cannot find the config file for modelopt". *Test the agent:* does it verify the quant is actually
  **applied** (weights resident FP8 + a block-scale grid), or assume "it's a modelopt export → stock
  modelopt serves it"? "Server returned 200" without checking the load path is a miss.
- **EV-AM-FUSED-QUANT-TARGET** — vLLM **fuses** `gate_proj`+`up_proj`→`gate_up_proj`
  (MergedColumnParallelLinear) on the LM path, but the diffusion-side quant target regex matches only
  the **unfused** names. A target rule written for the diffusion names silently **misses** the fused
  LM layer → it loads unquantized → FP8 bytes into a BF16 param. *Test the agent:* when reusing a
  diffusion-path quant method on the LLM path, does it target the **fused** module name?
- **EV-AM-REASONER-CONTAINER-WIRING** — Reasoning is now a **container** residency plane
  (`ContainerPlaneWorker`), not an in-api `SubprocessPlaneWorker` at `:8765`. A test asserting the
  subprocess/`reasoning_spec`/port-8765 wiring is **stale** and must be updated to the container
  path (per EV-AM-CPU-SUITE-GREEN's "update, never revert" rule), not reverted to keep it green.
