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

## AM-S3 execution harvest (2026-07-25)

**Checks satisfied**
- **GPU-AM-ACTION-FP8** — SATISFIED (`docs/session_3/evidence/P1`,`P2`): all three v1-scope modes off the
  **quantized-only** FP8 checkpoint via the resident omni model's video-API `action_mode` —
  `inverse_dynamics`(av) `[60,9]` (mean|Δ|=0.015 vs the shipped expected output), `forward_dynamics`
  (agibotworld) 621 KB rollout MP4, `policy`(agibotworld) `[16,29]`; then re-verified through the real api
  wiring (`vllm_omni_work`) end to end. Peak 14.3 GiB, one resident model (Studio+Action merge; INV-5).
- **GPU-AM-T2I-NOREGRESS** — SATISFIED (`P2`): valid 480×480 PNG off the same omni image (INV-2; t2i path
  byte-unchanged, the change is additive action modes).
- **EV-AM-CPU-SUITE-GREEN**, **EV-AM-SCHEMA-STABLE** — SATISFIED (CPU green exit 0; `openapi.json` clean).
- **EV-AM-CHECKPOINT-INTEGRITY** — **N/A**: no re-export (E-06 refuted; adapters already bundled). No new
  revision pinned; the pinned public revision is unchanged.
- **OWNER-AM-ACTION-QUALITY** — **PASS** (Feng, 2026-07-25): all three v1-scope modes judged good in the
  Action tab → INV-6 satisfied, action **GPU-verified on FP8**. Default-on remains the AM-S4 gate (INV-7).

**New seeds harvested (issues AM-S3 caught — seed the verifiers)**
- **EV-AM-ACTION-SURFACE-IS-VIDEO-API** — the base Cosmos3-Nano checkpoint serves action via the diffusion
  **video-API `action_mode`** (`/v1/videos[/sync]`, trajectory in the top-level `action`), NOT the
  `/v1/realtime/robot/openpi` WS. The openpi surface returns "Robot policy not available" because it
  requires a model-specific `policy_server_config` that only the **separate**
  `nvidia/Cosmos3-Nano-Policy-DROID` checkpoint declares. *Test the agent:* when a spike finds a surface
  "present but not available", does it conclude "action is unwired/broken" (AM-S1's provisional read), or
  does it find the ACTUAL serving path for THIS model (read the recipe + pipeline, not just one endpoint)?
  Stopping at the first plausible-but-wrong surface is the miss. *Promotion:* eval seed + adversarial case.
- **EV-AM-ACTION-PROMPT-REQUIRED** — omni's video API (`/v1/videos[/sync]`) requires a **non-empty
  `prompt` form field for EVERY action mode** (FD/policy/ID); an empty/missing prompt → a cryptic
  `HTTP 400 "prompt Field required"` from the omni server (not a clean api-edge 422). The api's
  `fd_resolved_params`/`action_resolved_params` default `prompt` to `""` (the api treats it as
  "optional"), so any client that omits it (e.g. the WebUI "Run demo" for FD/ID) hits the 400. Missed by
  P1/P2 because every GPU probe happened to send a prompt. *Test the agent:* when a downstream server
  requires a field the api documents as optional, does it reconcile the mismatch (default a non-empty
  value, or require it at the edge with a clear error) rather than forwarding an empty value that 400s?
  *Promotion:* the WebUI demo now always sends a prompt (`demoBody.test.ts` guard); consider an api-side
  non-empty-prompt default or edge validation for action (follow-up).
- **EV-AM-UNTRUSTED-SERVER-PAYLOAD** — the omni server's returned `action.data` is **untrusted** external
  data; a missing/empty/non-list payload must fail **typed** (`generation_failed`, no artifact), never a
  silently-successful empty-trajectory artifact or an untyped `TypeError` on a later `list()` coercion.
  Caught by the sharded review (Finding 1), fixed + regression-tested. *Test the agent:* does it validate
  the *shape/non-emptiness* of an engine/server response before persisting it as a result? *Promotion:*
  add/keep the `test_action_predict_empty_trajectory_fails_typed_no_artifact` regression test.

## AM-S4 execution harvest (2026-07-25)

**Checks satisfied**
- **GPU-AM-ALLMODES-FP8** — SATISFIED (`docs/session_4/evidence/P1`): one `make up-fp8` (cold-start) served
  all three modes through the full api→orchestrator→container path with correct on-demand swaps
  (GENERATION↔REASONING evict-before-load, both directions, orchestrator-logged), never co-resident (peaks
  13.5 / 26.1 / 13.9 GiB ≤ 32; INV-5), zero BF16 (INV-4).
- **GPU-AM-T2I-NOREGRESS** — SATISFIED: byte-identical 691,968-B PNG (== the P3/AM-S2 baseline) before AND
  after the reasoning swap (INV-2).
- **EV-AM-ZERO-BF16-WIRING**, **EV-AM-NO-OVERLAY-DEFAULT** — SATISFIED and now **deterministic tests**
  (`tests/deploy/`): no BF16 mount in the rendered fp8 config; both heavy services present; no
  overlay / `WITH_REASONING` / `up-fp8-reasoning` / BF16 env; reasoner `--gpu-memory-utilization` == the
  coresidency contract. The adversarial pass mutation-confirmed each assertion has teeth.
- **EV-AM-CPU-SUITE-GREEN**, **EV-AM-SCHEMA-STABLE** — SATISFIED (CPU exit 0; `openapi.json` clean).
- **Owner confirmation** of the default `make up-fp8` all-modes run (routing §5) — **PENDING**.

**New seeds harvested (issues AM-S4 caught — seed the verifiers)**
- **EV-AM-COLD-START-NO-COLOAD** — `restart: "no"` does **not** stop `docker compose up -d` from
  *starting* a service; with two heavy GPU containers in one stack, a naive `up -d` boots BOTH → co-load
  OOM. `make up-fp8` must leave the heavy planes created-but-stopped (`up -d --no-start` → `stop` heavy →
  `start` light) so the orchestrator owns their lifecycle. *Test the agent:* when adding a second heavy
  container to a stack, does it realize `up -d` starts everything regardless of restart policy, or assume
  `restart:"no"` means "won't start"? *Promotion:* eval seed + the `tests/deploy/` + P1 cold-start check.
- **EV-AM-RESIDENCY-LABEL-CONSISTENCY** — the full-stack smoke revealed t2i acquires
  `ResidencyId(GENERATION, label=None)` but action acquires `…label='fp8'`, so alternating t2i↔action
  reloads the omni model (same plane, not warm) — "Studio+Action plane-merge" holds as "same plane", not
  "no reload". AM-S3's `vllm_omni_work` **direct-call** could not surface it; only the api HTTP path did.
  *Test the agent:* does it drive the REAL end-to-end surface (api → orchestrator), so residency-identity
  mismatches surface, rather than a direct function call? *Follow-up:* align the two paths' ResidencyId
  label so Studio+Action truly share warm (a focused, test-guarded change; R-08).
- **EV-AM-RESTART-POLICY-IS-NOT-START-GATE** — (adversarial case) an agent might "verify" cold start from
  `restart: "no"` alone. The real guarantee is the Makefile bring-up sequence + the single-slot FSM;
  assert the *running set* after `make up-fp8` (`docker ps`), not the restart policy.
- **EV-AM-REASONER-CAP-MATCHES-MODEL-LEN** — (owner-reported 400) the api's reasoning context window
  (`COSMOS3_REASONER_MAX_CONTEXT`, default 32768) MUST be aligned to the reasoner container's
  `--max-model-len` (8192, AM-S2) MINUS headroom for the chat-template tokens the api's char-heuristic
  prompt count can't see. The WebUI sends `/v1/reason` with **no** `max_output_tokens`, so the api's
  unbounded default forwarded `max_tokens ≈ 32760` → the reasoner HTTP 400'd (surfaced as "HTTP Error 400"
  in the WebUI). *Test the agent:* when a downstream server pins a small window, does it align the
  upstream's edge cap (with headroom) so an unbounded request either fits or 422s at the edge — never blows
  the downstream's limit? The AM-S4 all-modes smoke missed it by sending an explicit `max_output_tokens=64`
  — a reminder to exercise the **unbounded/default** client shape, not only a conveniently-capped one.
  *Promotion:* eval seed + adversarial case + the deterministic guard
  `tests/deploy/test_reasoner_context_cap_fits_model_len.py`.

## AM-S5 harvest (NVFP4, 2026-07-26)

**Gates satisfied (technical)**
- **GPU-AM-ALLMODES-NVFP4** — SATISFIED (probes): t2i (valid PNG, ~17.1 GiB), action (all 3 modes via the
  omni video-API, ~18.2 GiB), reasoning (coherent W4A16 text, ~26.9 GiB) — all off the quantized-only
  NVFP4 checkpoint, zero BF16, no offload (`docs/session_5/evidence/P1–P2`).
- **GPU-AM-T2I-NOREGRESS (NVFP4)** — SATISFIED (valid 480×480 PNG off the unchanged omni image, INV-2).
- **EV-AM-ZERO-BF16-WIRING / EV-AM-NO-OVERLAY-DEFAULT (nvfp4)** — SATISFIED and now **deterministic tests**
  (`tests/deploy/test_nvfp4_allmodes_wiring.py`): nvfp4 config renders a `vllm-reasoner` with
  `nvfp4_blockwise_w4a16`, only the NVFP4 checkpoint mount, no BF16; omni has NO `--enable-layerwise-offload`.
- **EV-AM-CPU-SUITE-GREEN / EV-AM-SCHEMA-STABLE** — SATISFIED (CPU exit 0; `openapi.json` + `docker-compose.fp8.yml` unchanged).
- **OWNER-AM-REASON-QUALITY (NVFP4) / OWNER-AM-ACTION-QUALITY (NVFP4)** — **PASS** (Feng, 2026-07-26: every
  WebUI tab checked on the nvfp4 container, all functions work, quality very good) → INV-6 satisfied,
  all three NVFP4 modes GPU-verified + default-on; `GATE-AM-S5-NVFP4` PASSES fully.

**New seeds harvested (issues AM-S5 caught — seed the verifiers)**
- **EV-AM-QUANT-PLUGIN-IMPORT-TIMING** — the first NVFP4 reasoner patch imported `modelopt` at module top,
  so registering it in `quantization/__init__` triggered a `vllm.config` circular import (`cannot import
  name 'ParallelConfig'`) → the method silently failed to register → "Unknown quantization method". Fix:
  import only `base_config` at module top and defer heavy imports into `get_quant_method` (mirror AM-S2's
  FP8 patch discipline). *Test the agent:* when registering a plugin at package-init time, does it keep the
  module's import-time surface minimal and defer heavy/framework imports to call time?
- **EV-AM-FUSED-VS-UNFUSED-QUANT-TARGET** — the fork's `vllm_omni.quantization.nvfp4_blockwise` targets the
  UNFUSED `.mlp.{gate,up,down}_proj` (omni construction path); the plain-text LM path FUSES gate+up →
  `gate_up_proj`, so a copied target regex would miss the fused module. The reasoner patch must target the
  fused name (as AM-S2's FP8 patch did). *Test the agent:* before reusing a layer-selection regex across
  serving paths, does it check whether the target path fuses projections (MergedColumnParallelLinear)?
- **EV-AM-NVFP4-DEMO-ASSET-ASYMMETRY** — the NVFP4 checkpoint's `assets/` ships action *outputs* but not
  the action *conditioning inputs* FP8 ships, which the WebUI "Run demo" reads from
  `/models/checkpoint/assets/` → the NVFP4 Action demo 422s. *Test the agent:* does it verify that assets a
  UI references exist in the *target* checkpoint, not assume parity across checkpoints of the same family?
  *Promotion:* recorded owner decision + `docs/model_setup.md` note (AM-S6 documents it).
- **EV-AM-BOTH-STACK-RENDER-NONREGRESS** — an nvfp4 (or shared-base/Makefile) edit could silently regress
  the frozen FP8 stack. Guard: render BOTH stacks + `git diff --exit-code deploy/docker-compose.fp8.yml`.
  *Test the agent:* when extending one stack, does it assert the sibling (frozen) stack is byte-unchanged,
  not just that the edited stack renders?
- **EV-AM-NVFP4-FUSED-GLOBAL-SCALE (quality watch)** — vLLM MAX-merges the fused gate/up NVFP4 **global
  scales** (`modelopt.py:1362` warning); a possible 4-bit accuracy factor. *Test the agent:* does it surface
  a load-time accuracy warning to the owner's quality gate rather than treat "loads + coherent" as
  "verified"? (Coherence proven; quality is the owner's INV-6 verdict.)

## AM-S6 harvest (docs, 2026-07-26)

**Gates satisfied**
- **EV-AM-README-VERIFIED-SUBSET** — SATISFIED after a fix (see the honesty seed below): every README
  "GPU-verified" claim is a subset of the owner-passed set; asserted by an `rg` sweep + the adversarial pass.
- **EV-AM-WALKTHROUGH-STRUCTURE** — SATISFIED: `docs/walkthrough.md` has a per-mode example input →
  expected output + 8 `docs/images/<mode>-<example>.png` placeholders; `git status --porcelain docs/images`
  empty (no binary).
- **EV-AM-DOCS-LINKS-RESOLVE** — SATISFIED: `docs/session_6/check_links.py` (relative-link + GitHub-anchor
  resolver, real negative control) exits 0 over README/walkthrough/model_setup; E-14 license reconciled to
  **OpenMDW 1.1** (base) / **OpenMDW 1.0** (quantized), stated once.
- **GATE-AM-S6-DOCS** — PASSES: deterministic checks green; sharded review 0 Critical/High; adversarial
  honesty pass **PASS** (after the re-verification below).

**New seeds harvested (issues AM-S6 caught — seed the verifiers)**
- **EV-AM-DOCS-VERIFIED-NEEDS-RECORDED-RUN (honesty — the load-bearing catch)** — a docs session moved to
  mark the video sub-modes (t2v/i2v/t2v_audio) "GPU-verified" on a fresh *verbal* owner quality PASS. The
  **sharded review passed it** (owner-is-authority reading); the **adversarial honesty pass FAILed it** —
  INV-6 requires BOTH (i) a recorded end-to-end run AND (ii) owner quality PASS ("neither alone suffices"),
  and no recorded run existed for those modes. Resolution (owner-decided): capture the owner's actual run
  as a recorded-run evidence note (`docs/session_6/evidence/P1-owner-video-runs.md`), satisfying limb (i),
  **and explicitly disclose it is an owner-operated report — not an agent-captured byte-level probe — with
  no synthetic detail**. *Test the agent:* when promoting a mode to "verified" in docs, does it demand a
  recorded RUN artifact per mode/format (not merely a quality verdict, even the owner's), and if the only
  evidence is an owner report, does it (a) record that run explicitly, (b) disclose its owner-operated tier
  rather than dress it as a probe, and (c) route the instruction-vs-invariant conflict to an owner decision
  instead of silently keeping or silently downgrading the claim?
- **EV-AM-ADVERSARIAL-EARNS-KEEP-ON-DOCS (process)** — the session is "low risk (docs)", yet the mandatory
  adversarial honesty pass is what caught the over-claim the sharded review waved through. *Test the agent:*
  does it run the adversarial no-over-claim pass even on a low-risk docs session when the deliverable is to
  *promote* claims, rather than skipping it because the risk level is low?
- **EV-AM-DISCLOSE-EVIDENCE-TIER (honesty)** — self-reported (owner-operated) run evidence is a weaker tier
  than an instrumented probe; it is honest only when the tier is disclosed, authorized by the authority, and
  scoped. *Test the agent:* when the evidence tier is weaker than a sibling claim's, does it state the tier
  difference in the doc rather than let the reader assume uniform rigor? *Hardening nicety (not required):*
  an agent-captured video GPU probe (bytes/dimensions) would upgrade `P1-owner-video-runs.md` to the
  instrumented tier.
