# AM-S3 Design — Action enabled on FP8 (zero-BF16), serving-path reconciliation

Date: 2026-07-25 · Session: AM-S3 · Risk: high · Gate: `GATE-AM-S3-ACTION`.
Full exploration + approaches + spike rubric: `brainstorming.md`. This is the planned
architecture + decisions + capabilities. It was **branched** on the (a)-openpi spike (§Decisions D2);
the spike **resolved to (a2)** — see the banner below.

> **SPIKE OUTCOME (2026-07-25, GPU, `evidence/P1`) — resolves the branch to (a2); (c) not built.**
> `(a1)` openpi WS = **NO-GO** (it serves the separate `nvidia/Cosmos3-Nano-Policy-DROID` checkpoint,
> not the base). `(a2)` the omni **video-API `action_mode`** = **GO, GPU-PROVEN** for all three modes off
> the quantized-only FP8 checkpoint (`inverse_dynamics` av `[60,9]`, mean|Δ|=0.015 vs shipped expected;
> `forward_dynamics` agibotworld 621 KB rollout; `policy` agibotworld `[16,29]`; peak 14.4 GiB — action
> shares the omni footprint, **no extra plane**). **Decision (owner-confirmed): implement (a2) only** —
> extend `vllm_omni_work`/`client.py` for policy/ID (FD already wired), retire `COSMOS3_BASE_ACTION_DIR`,
> leave the `(c)` `diffusers_action` graft **dormant** (D3's `Plane.ACTION` is **NOT built**; R-11). The
> as-built spec is in `execution_contract.md`; D1/D1a/D3 below are retained as the (unused) fallback record.

**Process note (recorded adaptation, not silent).** Following AM-S1/AM-S2 practice and the
owner's "spike-lean docs" preference, this session consolidates the workflow's refining phases
into `brainstorming.md` (interview + exploration + approaches), this `design.md`
(proposal + design + capabilities), `execution_contract.md` (tasks + plan + checks, written
after the spike resolves the branch), and `decision_record.md` (spike outcome + gate scorecard).
No separate `proposal.md` / `specs/**` / `tasks.md` / `plan.md` tree is produced; the specs live
here and in the execution contract as testable requirements/scenarios.

## Context

AM-S1 refuted the blueprint's premises for action (see `docs/evidence_map.md` AM-S1 audit):
zero-BF16 action is **already achieved at the checkpoint level** (the FP8 checkpoint bundles the
5 BF16 `action_*` adapters), so AM-S3 is a **serving-path** session, not checkpoint-packaging.
Byte probe of the deployed FP8 checkpoint (`4e181f9`), torch-free:

- `quantization_config.json` (root): `recipe:"fp8_blockwise_mixed"`, `granularity:"blockwise-128x128"`,
  **`n_quantized_weight:216`**.
- transformer safetensors: 1246 tensors = **216 `F8_E4M3` + 1030 BF16**; **216 `_amax` / 0 `_double_scale`**
  (→ FP8); the **5 `action_*` adapters present** (BF16): `action_modality_embed`,
  `action_proj_in.{bias,fc}.weight`, `action_proj_out.{bias,fc}.weight`.

Action is two distinct surfaces: `forward_dynamics` (world-model video rollout) is **already wired**
via omni `POST /v1/videos/sync`; `policy`/`inverse_dynamics` (predict actions) have **no working
path** (omni openpi WS = "not available"; the in-process `(c)` graft is broken).

## Goals / Non-Goals

- **Goals:** action runs end-to-end on FP8 off the **quantized-only** checkpoint (zero BF16);
  `forward_dynamics` GPU-verified (anchor); `policy`/`inverse_dynamics` GPU-verified **or** an
  explicit recorded owner decision; `t2i` non-regressed; CPU suite green; `openapi.json` shape
  stable; owner action-quality PASS recorded (PENDING until signed).
- **Non-Goals:** reasoning (AM-S2); default-on merge + legacy cleanup (AM-S4); NVFP4 (AM-S5);
  README/walkthrough (AM-S6); deleting the dormant `gen_worker` generation path (R-11) unless it
  conflicts; a checkpoint re-export (none needed unless `integrity_probe` fails on the pinned rev).

## Capabilities

- **MODIFIED — action serving off the quantized checkpoint.** The `diffusers_action` load path
  stops grafting `action_*` from the BF16 base (`COSMOS3_BASE_ACTION_DIR`) and loads the
  checkpoint's own bundled adapters; precision verification is grounded in the checkpoint's
  `quantization_config.json` (recipe `fp8_blockwise_mixed`, count 216) instead of the frozen `505`.
- **NEW (branch (c) only) — `Plane.ACTION` residency plane.** A third GPU-resident plane serving
  `policy`/`inverse_dynamics` via the action-enabled diffusers pipeline in a killable subprocess
  worker, evict-before-load vs `GENERATION`/`REASONING` (INV-5). Generation stays 100% omni (INV-3).
- **NEW (branch (a) only) — omni openpi action bridge.** A WS client + `vllm_omni_work` dispatch so
  `policy`/`inverse_dynamics` REST jobs are served by the resident omni model, keeping the REST
  `/v1/action/*` async-job response shape unchanged (INV-8).
- **Env/mount surface (both branches):** `COSMOS3_BASE_ACTION_DIR` retired/redirected; the default
  action path requires no BF16 base mount (INV-4), asserted by `docker compose … config` + `rg`.

## Decisions

- **D1 — Loader fix (both branches; `api/engines/diffusers_action/loader.py`).** In
  `load_action_transformer`: drop `read_action_adapter_tensors(base_action_dir)` and the
  `merge_state_dicts` graft — `from_config(action_gen=True)` → `restore_from_modelopt_state` →
  `load_state_dict(strict=True)` over the checkpoint's **own** 1246 tensors (which already include
  the 5 `action_*`). Replace `GEN_TOWER_QUANTIZED=505` with the count **derived from the
  checkpoint** (`quantization_config.json`'s `n_quantized_weight`, = 216), keeping the precision
  discriminator gate (declared==observed). Rejected: keep the base graft (collides; needs BF16 base
  → INV-4 breach); keep 505 (fails the count gate at 216).
- **D1a — D1-FP8 verify fix + blast-radius.** The recipe/count checks live in
  `api/engines/diffusers_oracle/{config,loader}.py` (`precision_from_quant_config` rejects
  `fp8_blockwise_mixed`; `verify_precision` defaults to 505) — **outside** the AM-S3 blast radius.
  Plan: keep the action loader's verification **self-contained** in `diffusers_action` (read the
  recipe/`n_quantized_weight` from the quant config and assert directly), so no oracle edit is
  needed. If a shared fix is cleaner, request an **owner blast-radius amendment** (AM-S2 precedent)
  — recorded, never silent. **Decided in the execution contract after the spike.**
- **D2 — Spike-first branch (owner: spike (a) then (c)).** Time-boxed GPU probe of omni
  `/v1/realtime/robot/openpi` under the pre-registered rubric (`brainstorming.md §5`). (a)-GO ⇒
  openpi bridge (config-only, no fork change, no INV-8 shape change); (a)-NO-GO ⇒ (c) below.
- **D3 — (c) plane = third `Plane.ACTION`, subprocess worker (owner-approved Approach A).** Add
  `Plane.ACTION`; `_plane_for_mode` routes `policy`/`inverse_dynamics` → `ACTION`; a dedicated
  action subprocess worker reuses `gen_worker`'s `build_adapters`/`dispatch` (action view) via a new
  `action_spec(...)` + `SubprocessPlaneWorker`; `default_worker_factory` gains an `ACTION` branch;
  the action job `work` is the IPC `gen_plane_work` pointed at the action socket. The single-slot FSM
  is unchanged (evict-before-load; INV-5). Rejected: engine-swap in the generation slot (overloads
  the plane, risks t2v-on-diffusers); a diffusers-action container (new ~13 GiB image, redundant).
- **D4 — `forward_dynamics` stays on omni video-sync (both branches).** No new plane for FD; it runs
  on `Plane.GENERATION` via `vllm_omni_work` as today. FD GPU verification must confirm the rollout
  is **action-conditioned** (not a plain video) — part of the owner quality gate.
- **D5 — Zero-BF16 env/mount.** Retire the `COSMOS3_BASE_ACTION_DIR` default in
  `diffusers_action/loader.py` and `.env.example`; ensure `deploy/docker-compose.{base,fp8}.yml`
  mount no BF16 base for action (INV-4).

## Risks / Trade-offs

- **[(a) openpi may be a missing backend, not a flag — unbounded fork lift]** → the pre-registered
  rubric time-boxes it; NO-GO falls to (c) (D2/D3). Mitigation: rubric + owner-confirmed strategy.
- **[(c) in-process diffusers load past D1 unproven on GPU]** → byte analysis shows D1-FP8 is only
  the recipe-string + count-constant (both fixed by D1/D1a); the modelopt restore + strict load are
  the residual GPU unknown → the (c) GPU verification is the proof. If the restore/strict-load fails
  for a reason beyond D1/D1a, policy/ID become an explicit owner decision (INV-4/INV-7), FD anchors.
- **[FD omni path ignores action `extra_params` → plain video]** → the FD GPU check confirms
  action-conditioning; owner quality gate rules on trajectory realism.
- **[Dropping the base graft breaks graft-pinned tests (R-11)]** → update `test_action_loader_unit`
  (collision/base-dir) to the checkpoint-tensors path; keep `merge_state_dicts` as a tested pure
  Calculation only if still used, else remove with tests.
- **[New `Plane.ACTION` touches the orchestrator FSM enumerations]** → within blast radius
  (`api/orchestrator/**`); the FSM mechanism (evict-before-load) is unchanged, only a new plane id +
  factory branch + job mapping; CPU residency/selection tests guard it.
- **[VRAM: action pipeline (~13 GiB) + omni (~13.5 GiB) co-resident → OOM]** → never co-reside
  (evict-before-load, INV-5); Studio+Action plane-merge (if (a)) is projected, **measured** before
  any claim.

## Migration Plan

Transitional this session: FP8 action works off the quantized checkpoint by the chosen mechanism;
`COSMOS3_BASE_ACTION_DIR` retired/redirected. AM-S4 folds action into the clean default-on `make
up-fp8` all-modes stack + full smoke. Rollback: revert the AM-S3 diff; the dormant `gen_worker`
generation path and the omni FD path are otherwise untouched. No checkpoint re-export, so no
revision change unless `integrity_probe` fails on the pinned public revision (then NFR-5 re-pin).

## Open Questions (resolved by the spike / execution contract)

- policy/ID mechanism → the (a)-openpi spike (D2).
- D1-FP8 verify fix location (self-contained vs oracle amendment) → execution contract after the
  spike (D1a).
- If (a): does the openpi bridge need a new WS transport in `vllm_omni/client.py`, and does the
  policy response map to the existing trajectory-JSON artifact without an INV-8 change? → spike.
