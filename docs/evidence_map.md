# Evidence Map - All Modes, GPU-Verified, Default-On

Date: 2026-07-24

Rules:

- Claims without evidence are marked speculative.
- Speculative and **spike-gated** claims cannot become MUST-level requirements;
  they inform session objectives and gates, not shipped capabilities.
- Owner decisions can become contract constraints, but technical feasibility
  still needs verification by the owning session (and, for output quality, the
  owner's manual gate).
- This repository is public. Entries must not cite private hosts or bake in
  private absolute paths; environment variables are cited by name only.
- Evidence IDs restart per phase; cross-phase facts are cited to their archived
  location. All `file:line` citations are against the tree at 2026-07-24 and are
  re-confirmed by the owning session before it edits.

## A. Current architecture — direct source inspection, 2026-07-24

| Claim | Evidence | Source | Confidence | Gap / Risk |
|---|---|---|---|---|
| E-01 The three modes run in **different processes/engines** today: Studio via the `vllm-omni` container; Reasoning via a separate `vllm serve` subprocess; Action grafted into the in-process `diffusers` engine (dormant by default). | `default_worker_factory` branches: `Plane.REASONING` → `reasoning_spec(...)` `SubprocessPlaneWorker`; generation → `vllm_omni` `ContainerPlaneWorker` (default) **xor** dormant `diffusers` `gen_worker` (`api/app/main.py:94-156`). | Direct source inspection | High | The modes are not symmetric; "enable all in one stack" is not a single compose merge. |
| E-02 `vllm-omni` is a `vllm serve … --omni` OpenAI-compatible fork serving the quantized checkpoint on :8000. | `CMD ["vllm","serve","/models/checkpoint","--omni","--host","0.0.0.0","--port","8000","--init-timeout","1800"]` (`deploy/vllm-omni.Dockerfile:40`, base `vllm/vllm-openai:v0.24.0` `:9`, pin `:13`); stack `command:` adds `--no-guardrails`/tiling (`deploy/docker-compose.fp8.yml:20-33`). | Direct source inspection | High | Because it is a vLLM OpenAI server, `/v1/chat/completions` (reasoning) is *natively* in scope — the basis for option (a) (spike-gated, S-A). |
| E-03 Each quantized checkpoint is **self-contained** for the diffusers pipeline and ships an LM chat template + tokenizer. | "Each checkpoint is self-contained … ships `model_index.json`, `config.json`, `generation_config.json`, `vae/`, `text_tokenizer/`, `vision_encoder/`, `sound_tokenizer/`, `scheduler/`" (`docs/model_setup.md:33-34`); the repo also ships `chat_template.json`, `tokenizer.json`, `merges.txt`, `vocab.json` (checkpoint dir listing). | Direct source inspection | High | Supports zero-BF16 reasoning: the LM-serving assets are present in the quantized repo. |
| E-04 Reasoning today is a **separate `vllm serve` subprocess** (port 8765, `/health` probe, `--enforce-eager`) at `COSMOS3_REASONER_MODEL_DIR` (the BF16 base), gated by the `WITH_REASONING=1` build (torch + vLLM 0.23.0). | `reasoning_spec(ReasonerConfig, vllm_bin, port, ...)` → `PlaneSpec(plane=REASONING, probe=/health, strip_parent_env=True)` (`api/orchestrator/planes.py:49-64`); constructed at `api/app/main.py:128-134`; build split `ARG WITH_REASONING=0` / `FROM base-${WITH_REASONING}` / `uv pip install vllm==0.23.0` (`deploy/api.Dockerfile:10,22,37-39`); overlay wires it (`deploy/docker-compose.reasoning.yml`). | Direct source inspection | High | Reasoning is a build-time + overlay-time opt-in, not a default. |
| E-05 A plain `make up-fp8` ships **no reasoner**; only `make up-fp8-reasoning` (overlay) does — and the owner reports reasoning is not actually working even then. | `up-fp8: $(COMPOSE) $(FP8) up -d` vs `up-fp8-reasoning: $(COMPOSE) $(FP8) $(REASON) up -d` (`Makefile`); reasoner dir defaults to the BF16 base (`.env.example:52`). | Direct source inspection + owner report | High (unreachable-by-default) / Medium (the "even the overlay is broken" report is not independently reproduced here) | `AM-S1` reproduces the current reasoning state before rebuilding it. |
| E-06 **Action requires bf16 `action_*` adapter tensors read from the BF16 base transformer; the quantized checkpoint ships without them**, and the load raises `FileNotFoundError` if they are absent. | "Enables `action_gen=True` on a quantized … checkpoint that ships **without** action tensors, by grafting the base-model bf16 action adapters"; `read_action_adapter_tensors(base_action_dir)` reads only `action_*` keys and `raise FileNotFoundError` if none (`api/engines/diffusers_action/loader.py:1-3,74-92`); default `COSMOS3_BASE_ACTION_DIR=/data/models/Cosmos3-Nano/transformer` (`:36`). | Direct source inspection | High (code) / **REFUTED at checkpoint (AM-S1)** | **Zero-BF16 action is a checkpoint-packaging problem**, not a serving-config one (R-01). **⚠ AM-S1 (2026-07-24): E-06 REFUTED against the real checkpoint — the quantized FP8 (deployed `4e181f9` + pinned public `9bf5d6ae`) and NVFP4 already ship the 5 BF16 `action_*` tensors (`action_gen:true`, real values); the gap was closed by the prior P6-S5 `checkpoint_prep mutate`. Not a live blocker — see the AM-S1 execution audit below + R-01.** |
| E-07 Action is implemented only under the **dormant `diffusers` engine**; the default `vllm_omni` container's action-serving path is unverified/absent. | Generation runs `vllm_omni` by default, `diffusers` is "(dormant)" (`api/app/main.py:94-110`); action route enqueues jobs onto the shared runner (`api/app/routes/action.py:43-64`), whose `work` is `vllm_omni_work` by default (`api/app/main.py:108-110`); the matrix lists action's serving path as the "in-process `diffusers_action` graft" (`docs/model_setup.md:81`). | Direct source inspection | High | Serving action via `vllm-omni` (option a) is unproven; the `(c)` side-car fallback exists (spike-gated, S-C). |
| E-08 A **single-slot residency FSM** swaps `Plane.GENERATION` ↔ `Plane.REASONING` by process-kill (evict-before-load); the two heavy residents **never co-reside** in the 32 GiB budget. | `class Plane(GENERATION, REASONING)` (`api/orchestrator/planes.py:20-24`); `CoResidencyContract(mechanism="stop_start", eviction="process_kill")`, `VRAM_BUDGET_BYTES = 32*1024**3`, reasoner ~16 GiB bf16 → ~26 GiB @ `gpu_memory_utilization=0.85`, generation ~9 GiB; "planes never CO-reside … room freed by the process KILL" (`api/engines/vllm/coresidency.py:19-42`). | Direct source inspection | High | Under zero-BF16 the VRAM math changes (reasoner becomes ~quantized); the swap discipline is the safety net (INV-5, R-08). |
| E-09 On-demand switching already works: one shared GPU lease serializes the job runner and the reasoning stream, and `acquire` evicts-before-loads so a different-residency request preempts immediately. | `gpu_lease = asyncio.Lock()` shared by the runner and the reasoning route (`api/app/main.py:186-189`); orchestrator `acquire` cancels the idle timer and evicts-before-load (E-16; `api/orchestrator/manager.py`). | Direct source inspection | High | "Auto-switch backend models on demand" is largely built; the phase reuses it, it does not reinvent it. |
| E-10 There are **three deploy postures**, none "all modes": `fp8` and `nvfp4` stacks each `include:` the base; a reasoning overlay adds the BF16 reasoner. | `include: docker-compose.base.yml` (`deploy/docker-compose.fp8.yml:4`, `…nvfp4.yml:4`); overlay `deploy/docker-compose.reasoning.yml`; `up-fp8` / `up-nvfp4` / `up-fp8-reasoning` (`Makefile`). | Direct source inspection | High | `AM-S4` collapses these to two all-modes stacks. |
| E-11 Only **text→image** is GPU-verified end to end (FP8 + NVFP4, `GPU-S3`); every other mode is "implemented · CPU-tested · GPU gate (`MIG-S8`)". | `README.md` Features/Status; per-mode matrix (`docs/model_setup.md:76-84`): `t2i` "T2I-verified (`GPU-S3`)", reasoning/action/`t2v*` "GPU-unverified (`S8`)". | Direct source inspection | High | The `t2i` non-regression baseline (INV-2) and the honesty invariant (INV-6) anchor here. |
| E-12 The WebUI already ships **all three tabs**, fully wired and unconditional (Studio `/studio`, Reasoning `/chat` → `/v1/reason`, Action `/action` → `/v1/action/*` with a 3D URDF viewer). No feature flag gates them. | `PrimaryNav` items `Studio`/`Reasoning`/`Action`/`History` (`webui/app/_components/PrimaryNav.tsx:9-14`); chat stream → `/api/v1/reason`; action workspace → `/v1/action/{forward_dynamics,inverse_dynamics,policy}` (WebUI investigation, 2026-07-24). | Sub-agent investigation (not all lines re-opened here) | Medium-High | Frontend is out of scope; a session touches WebUI only on a verification-surfaced bug (R-12). Re-confirm at `AM-S6`. |
| E-13 The repo ships a **checkpoint-prep toolkit** (safetensors mutation/rewrite/copy + integrity probe) with its own tests. | `tools/checkpoint_prep/{mutation,rewrite,copy_shared,safetensors_io,integrity_probe,__main__}.py`; `tests/checkpoint_prep/test_*` (rewrite/mutation/copy/integrity/writer-format). | Direct listing | High (exists) / Medium (that it can add action tensors specifically) | Plausible home for bundling action adapters into the quantized checkpoint (FR-3); the exact capability is an `AM-S1`/`AM-S3` finding. |
| E-14 **License discrepancy (owner vs repo).** The repo's authoritative setup doc and README state the BF16 base (`nvidia/Cosmos3-Nano`) is license `other`; the owner states it is `openmdw-1.0`. | `docs/model_setup.md:15,24` ("`other`"; "MUST NOT describe the weights as MIT"); `README.md` checkpoint table ("`other`"); owner statement (2026-07-24). | Repo docs vs owner statement | **Low (unresolved conflict)** | Moot if zero-BF16 succeeds; load-bearing only if BF16 is ever reintroduced. The HF repo's own license page is the tie-breaker; do not encode either claim as fact until `AM-S6` reconciles it. |
| E-15 Guardrails are **off by design** on the local appliance (`--no-guardrails`); the guardrail model is not bundled. | `--no-guardrails` in both stack commands (`deploy/docker-compose.fp8.yml:31`, `…nvfp4.yml:32`); "Guardrails stay ON by default here; `--no-guardrails` is an explicit runtime override" (`deploy/vllm-omni.Dockerfile:37-39`); README Status & security. | Direct source inspection | High | Out of scope this phase; unchanged. Enabling more modes does not change the guardrails posture. |
| E-16 Idle keep-warm holds the resident plane 30 min (`LX-S1`); a different-residency request preempts immediately. | `idle_timeout = float(os.environ.get("COSMOS3_IDLE_TIMEOUT_SECONDS","1800"))` (`api/app/main.py:175`); `acquire` cancels the idle timer + evicts-before-load (`api/orchestrator/manager.py`; archived `docs/archive/phase-4/evidence_map.md` E-02/E-05). | Direct source inspection + phase-4 archive | High | Under zero-BF16, a mode swap reloads a ~quantized (not ~26 GiB BF16) model, so swaps get cheaper — a side benefit, not a requirement. |
| E-17 The action adapters are **small, selectively read, bf16** — feasible to bundle into a checkpoint. | `read_action_adapter_tensors` opens shards with `safe_open` and takes only `action_modality_embed`/`action_proj_in.*`/`action_proj_out.*` via selective `get_tensor` ("only the action tensors' byte ranges are read, not the full multi-GB shards") (`api/engines/diffusers_action/loader.py:74-92`); `GEN_TOWER_QUANTIZED = 505`, action adapters add none (`:37`). | Direct source inspection | High | Bundling them into the quantized export is a small, targeted mutation — supports FR-3 feasibility (still spike-gated, S-E). |

## B. Spike-gated / speculative claims (NOT promotable to MUST)

These are the load-bearing *unknowns*. Each is resolved only by running on the
RTX 5090; none may be written as a shipped capability until its gate passes.

> **AM-S1 (2026-07-24) resolved S-A, S-C, S-E and refuted E-06** — see the AM-S1
> execution audit at the end of this file. S-B (reasoning quality) and S-D (NVFP4)
> remain for AM-S2 / AM-S5. Directions: **S-A → reasoning `(c)`, zero-BF16 reasoning
> unproven; S-C → action `(a)`-surface-present-but-unwired / `(c)`-broken → serving
> work (prefer `a`); S-E → packaging GO & already applied (P6-S5).**

| ID | Claim (to be tested) | Why plausible | Resolving gate |
|---|---|---|---|
| S-A | `vllm serve --omni` on the **quantized** checkpoint answers `/v1/chat/completions` with coherent reasoning. | It is a vLLM OpenAI server (E-02) and the quantized repo ships a chat template (E-03). | `AM-S1` (runs) + `AM-S2` owner quality gate. |
| S-B | Quantized-transformer reasoning **quality** is acceptable to the owner (per format; NVFP4 4-bit is the riskier case). | FP8 is a mild quantization; NVFP4 is 4-bit and unproven for this LM path. | Owner manual gate at `AM-S2` (FP8) / `AM-S5` (NVFP4). |
| S-C | Action can be served by `vllm-omni` (option a); else a side-by-side `(c)` backend serves it. | Unknown whether the omni server exposes an action surface; the diffusers graft is the only known action implementation (E-07). | `AM-S1` decision + `AM-S3`. |
| S-D | NVFP4 4-bit supports the reasoning/action inference path on Blackwell (sm_120). | NVFP4 `t2i` works via a Marlin FP4 kernel that "repacks weights on CUDA after load" (`deploy/docker-compose.nvfp4.yml:15-20`); the LM/action paths are unproven. | `AM-S5`. |
| S-E | Bundling bf16 `action_*` adapters into the quantized checkpoint (via `tools/checkpoint_prep/`) yields a working **zero-BF16** action checkpoint without regressing `t2i`. | The adapters are small/selective (E-17) and a mutation toolkit exists (E-13). | `AM-S1` path decision + `AM-S3` (re-pin + `t2i` re-verify). |

## C. Owner-decision markers (binding as constraints; feasibility still gated)

- **Binding constraints (testable as *form*):** zero-BF16 default (no BF16 mount /
  overlay / `WITH_REASONING` in the default stacks — testable via `docker compose
  … config` + build args); `t2i` non-regression (a re-run smoke); "verified"
  requires the owner's recorded quality PASS; default-on only for gate-passing
  modes; two stacks only; single README + separate `docs/walkthrough.md`.
- **Owner value judgments (not evidence-derived, not auto-gated):** whether
  reasoning/action output quality is "good enough" (S-B) — this is *defined* to be
  the owner's manual verdict, so it is a human gate, not a deterministic check.
- **Speculative, not promoted to MUST:** that option (a) is achievable for action
  (S-C); that NVFP4 serves every mode (S-D); that a single re-exported checkpoint
  satisfies both `t2i` and action with no quality loss (S-E). These inform session
  objectives and fallbacks, never blueprint-time MUSTs.

## D. Fixed references (unchanged this phase unless a session says so)

- Public checkpoints and the `vLLM-Omni` pin: `docs/model_setup.md` §1, §9,
  `.env.example`. `AM-S3`/`AM-S5` may introduce a **new** action-bundled checkpoint
  revision; if so it is pinned and recorded there (NFR-5), and the existing `t2i`
  revisions are re-verified, not replaced silently.
- Guardrails-off (E-15), no application auth, loopback-by-default: unchanged.
- Idle keep-warm 1800 s (E-16): unchanged.

*(Execution audits and harvested evidence are appended by each session as it
closes, following the phase-4 pattern: an "`AM-S{n}` execution audit" block with
the standard GPU evidence fields — hardware, driver/CUDA, checkpoint repo +
revision, request shape, peak VRAM, guardrails posture, artifact metadata, result,
and the owner's quality verdict.)*

## AM-S1 execution audit (2026-07-24)

**Hardware/env:** RTX 5090 (sm_120), 32607 MiB, driver 610.43.03. FP8 probe via
`cosmos3-nano-vllm-omni:local` (fork `fengwang/vllm-omni@6970350`, base
`vllm/vllm-openai:v0.24.0`), command `--omni --no-guardrails --vae-use-tiling
--enable-layerwise-offload`. Checkpoint = `COSMOS3_FP8_DIR` (deployed rev `4e181f9`;
pinned public `9bf5d6ae` cross-checked on HF). Guardrails off (local posture, E-15).
CPU baseline `uv run pytest -m "not gpu"` = **523 passed** (unchanged). Full
evidence: `docs/session_1/` (P1–P7, decision_record, sharded_review,
adversarial_verification). No production/checkpoint file modified.

- **E-06 — REFUTED against the real checkpoint.** FP8 (deployed + pinned public) and
  NVFP4 transformers ship the 5 BF16 `action_*` adapters (`action_gen:true`, real
  values; header scan + byte sample). The gap was real at raw quantization and was
  closed by the prior **P6-S5 `checkpoint_prep mutate`** (sidecar
  `n_weight_quantized:216`, `appended_action_keys`, `lm_head_restored_bf16:true`).
  Residual = a serving-code reconciliation (AM-S3), not packaging.
- **S-A — reasoning `(c)`; zero-BF16 reasoning UNPROVEN.** `vllm serve --omni`
  `/v1/chat/completions` returns **images**, not text (image-gen bound;
  `response_format:text` still image; `modalities:[text]`→HTTP 500). Reasoning is not
  served by the omni path → `(c)` side-car. Zero-BF16 reasoning has no proven path →
  owner decision (new risk **R-15**).
- **S-C — action `(a)` surface present-but-unwired; `(c)` broken.** Omni exposes
  `/v1/realtime/robot/openpi` (WS, HTTP 101) — action IS an omni surface (**E-07
  partially refuted**) — but returns "Robot policy not available". In-process `(c)`
  graft raises a key-collision (checkpoint already has the tensors) + stale `505`
  precision constant (D1 confirmed). Neither functional as-served → AM-S3
  serving-path work off the checkpoint's own weights; **prefer `(a)`**; `(c)` fallback
  retained (R-02).
- **S-E — zero-BF16 action packaging GO, already applied (P6-S5).** No re-export
  needed for action.
- **S-B / S-D — untouched** (reasoning quality moot until text serves; NVFP4 = AM-S5).
- **Residency:** omni generation resident ≈ **13.2–13.5 GiB / 32**; idle 18 MiB;
  Studio+Action can **plane-merge** (same omni model, projected — unmeasured wired);
  reasoning stays a **separate plane (swap)**, E-08 BF16 math holds today.
  `/v1/omni/sleep|wakeup` = fork-native residency control (AM-S4 note).
- **Gate:** `GATE-AM-S1-SPIKE` technical parts satisfied; sharded review (no
  surviving Critical/High) + adversarial verifier **PASS**. Owner sign-off: ✅ **Feng, approved 2026-07-24**
  (`docs/session_1/decision_record.md` §8) — **GATE-AM-S1-SPIKE PASSES**. Directions:
  reasoning → investigate omni text-tower first (AM-S2); action → `(a)` omni robot
  policy + `(c)` fallback (AM-S3).
