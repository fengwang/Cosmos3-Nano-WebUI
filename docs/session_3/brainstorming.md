# AM-S3 Brainstorming — Action serving-path reconciliation (FP8, zero-BF16)

Date: 2026-07-25 · Session: AM-S3 · Risk: high
Inputs: `docs/prd.md`, `docs/project_contract.md`, `docs/session_3{,_contract}.md/yaml`,
AM-S1 (`docs/session_1/`), AM-S2 (`docs/session_2/`), and direct source inspection
(`api/engines/diffusers_action/**`, `api/orchestrator/**`, `api/engines/vllm_omni/**`,
`api/app/**`, `api/jobs/**`).
Owner intent confirmed via interview (2026-07-25) — see §1.

## 1. Confirmed intent (interview outcome)

- **Division of labor:** agent drives code + CPU tests + GPU end-to-end probes on the 5090
  + evidence; owner runs custom prompts and signs `OWNER-AM-ACTION-QUALITY` (recorded
  **PENDING** until signed). Same pattern as AM-S1/S2.
- **Mechanism strategy:** spike **(a)**-openpi first (time-boxed GPU probe); fall back to
  fixing **(c)** the `diffusers_action` graft if (a) is an unbounded omni-fork lift.
- **Mode scope:** best-effort all three; **`forward_dynamics` is the anchor** that must
  land GPU-run. If `policy`/`inverse_dynamics` can't reach a working path after the (a)
  spike + a (c) attempt, that is an **explicit recorded owner decision** (INV-4/INV-7),
  not a silent gap or an over-claim.

## 2. Refined problem (supersedes the blueprint's stale premises)

`session_3.md` was written under premises AM-S1 **refuted**. The real state:

| Piece | Real state (AM-S1 + source) | Work |
|---|---|---|
| Zero-BF16 action | **Already true** at the checkpoint level — FP8 (`4e181f9`; public `9bf5d6ae`) already bundles the 5 BF16 `action_*` adapters (`action_gen:true`). E-06 refuted; R-01 resolved. | **No re-export.** In-Scope item 1 of `session_3.md` is moot. |
| `forward_dynamics` | **Already wired**: omni `POST /v1/videos/sync` + action `extra_params`, on `Plane.GENERATION` via `vllm_omni_work` (`_SUPPORTED_MODES` includes it). GPU-**unverified**. | GPU-verify it is *actually action-conditioned* (the anchor). |
| `policy` / `inverse_dynamics` | **No working path.** `vllm_omni_work` rejects them (`unsupported_mode`); omni openpi WS `/v1/realtime/robot/openpi` returns `"Robot policy not available"`; the `(c)` path's **only** break is `loader.load_action_transformer`. | Spike (a); else fix loader + wire a plane. |

**Key finding — the `(c)` machinery already exists and is CPU-tested.**
`orchestrator/gen_worker.py` loads the action-enabled pipeline once, wraps it in both
`DiffusersOracleAdapter` (generation) and `DiffusersActionAdapter` (action), and its
`dispatch` + `_encode_action_reply` already handle **all three** modes
(FD/policy → rollout MP4 + trajectory sidecar; ID → trajectory JSON). The **only** broken
code is inside `loader.load_action_transformer`:

1. `merge_state_dicts(gen_tensors, read_action_adapter_tensors(base_action_dir))` **collides**
   on the 5 `action_*` keys — the checkpoint already ships them (E-06 refuted).
2. `GEN_TOWER_QUANTIZED = 505` ≠ the checkpoint's actual **216** F8 tensors (drift D1).

**Architectural constraint.** `_plane_for_mode` (`api/app/jobs_router.py:94`) routes **all**
action modes to `Plane.GENERATION`, and the diffusers `gen_worker` only runs under
`COSMOS3_GEN_ENGINE=diffusers` — which also routes **t2v/t2i** through diffusers, breaking
INV-3 and regressing `t2i`. Therefore `(c)` for policy/ID **must** run as action's *own*
residency plane, never by flipping the generation engine.

## 3. Branched plan (spike-first)

```
Task 0 — Spike (a)-openpi on GPU (time-boxed; pre-registered rubric §5)
├── (a)-GO  → BRIDGE: REST /v1/action/{policy,inverse_dynamics} → WS client to omni openpi.
│             policy/ID served by the resident omni model (Studio+Action plane-merge). No new plane.
│             INV-8: the REST /v1/action/* response stays the async-job shape (no schema change).
└── (a)-NO-GO → (c) FALLBACK: fix loader.py + third Plane.ACTION (§4).
forward_dynamics: stays on omni video-sync in BOTH branches (verified separately; the anchor).
```

## 4. `(c)` fallback design — action as its own residency plane (**Approach A, owner-approved**)

**Loader fix** (`api/engines/diffusers_action/loader.py`, ACD-clean):
- Stop reading `action_*` from the BF16 base. The checkpoint's own shards already carry the
  5 adapters (they load into `gen_tensors`), so `load_state_dict(strict=True)` succeeds with
  no graft. Remove the `merge_state_dicts(…, read_action_adapter_tensors(base))` call and the
  `base_action_dir` dependency from the load path.
- Replace hard-coded `GEN_TOWER_QUANTIZED = 505` with the value **derived** from the loaded
  checkpoint (verify against the sidecar/`read_quant_config`, not a frozen constant).
- Retire/redirect `COSMOS3_BASE_ACTION_DIR` (INV-4): drop its default; if any code still
  reads it, redirect to the quantized checkpoint dir. `merge_state_dicts` /
  `read_action_adapter_tensors` may remain as dead-but-tested pure Calculations or be removed
  with their tests updated (R-11) — decided in design.

**Plane wiring — Approach A (third `Plane.ACTION`):**
- Add `Plane.ACTION` to the `Plane` enum.
- `_plane_for_mode`: `policy`/`inverse_dynamics` → `Plane.ACTION`; `forward_dynamics` +
  generation modes → `Plane.GENERATION` (FD stays omni).
- A dedicated **action subprocess worker** reusing `gen_worker`'s `build_adapters`/`dispatch`
  (action view; the oracle view is unused on this plane), launched by a new
  `action_spec(...)` (mirrors `generation_spec`, READY_FILE probe) via `SubprocessPlaneWorker`.
- `default_worker_factory` gains a `Plane.ACTION` branch; the runner's `work` for action jobs
  is the IPC `gen_plane_work` (or a thin action variant) pointed at the action worker's socket.
- The single-slot FSM already evicts-before-load, so ACTION never co-resides with GENERATION
  or REASONING (INV-5); **generation stays 100% omni** (INV-3 safe).

**Rejected alternatives:** B (engine-swap inside the generation slot — overloads the plane,
complicates residency identity, risks t2v-on-diffusers); C (diffusers-action container —
needs a new ~13 GiB image, redundant with the existing subprocess).

## 5. Pre-registered spike rubric (freeze before running — anti-rationalization)

**Probe.** Launch the deployed omni image against the FP8 checkpoint; connect to
`/v1/realtime/robot/openpi` with a minimal valid `policy` request for an in-scope embodiment
(agibotworld, 29-D). Inspect: the WS response, container logs, and the vllm-omni fork's
`launcher.py`/recipe for a **policy-enable flag or policy-model path**.

**Decision (frozen):**
- **(a)-GO** *iff* there is an **operator-settable serving flag / config / model-path**
  (config-only, **no vllm-omni fork source change**) that makes openpi return a valid action
  from the checkpoint's own action weights, **and** the openpi request/response can be bridged
  to the REST `/v1/action/*` async-job schema **without** an INV-8 shape change. Time-box ≈ 1–2h.
- **(a)-NO-GO → (c)** if enabling the policy needs a **fork source change** (a code lift),
  OR the backend is absent with no config path, OR bridging would force an INV-8 schema change.

**FD is orthogonal:** verified via video-sync regardless of the (a)/(c) outcome for policy/ID.

## 6. Invariant / risk handling (both branches)

- **INV-2 / R-05:** GPU `t2i` non-regression smoke after any serving change (`GPU-AM-T2I-NOREGRESS`).
- **INV-3:** generation stays omni; diffusers serves **action only** (contract-sanctioned `(c)`).
- **INV-4:** no BF16 — `COSMOS3_BASE_ACTION_DIR` retired/redirected; asserted via
  `docker compose … config` (no BF16 mount) + an `rg` sweep.
- **INV-5:** single-slot evict-before-load preserved; a plane-merge is claimed only with a
  measured OOM-free VRAM trace (Studio+Action merge, if (a), is projected — measure before claiming).
- **INV-6:** verified = recorded GPU run **and** owner quality PASS.
- **INV-8:** `openapi.json` shape unchanged; an (a) WS bridge keeps the REST async-job response.
- **R-11:** dropping the base graft breaks `test_action_loader_unit` (collision/base-dir tests)
  → update to the checkpoint-tensors path, don't revert.
- **FD anchor risk:** omni may ignore the action `extra_params` and emit a plain video — the FD
  GPU check must confirm real action-conditioning (part of the owner quality gate).
- **No re-export expected:** if `integrity_probe` ever fails on the pinned public revision, that
  (and only that) triggers the NFR-5 re-pin path; otherwise none.

## 7. Open questions (resolved or deferred)

- *Which policy/ID mechanism?* → decided by the spike (§5).
- *(c) plane shape?* → Approach A (owner-approved).
- *Commit cadence?* → follow the workflow: commit only at clean checkpoints if the owner asks;
  otherwise leave a clean diff. (Not blocking.)
