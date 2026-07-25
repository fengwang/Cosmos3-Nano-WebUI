# Session Handoff

## State Snapshot
- Session: **AM-S3** — Action enabled + GPU-verified on FP8, **zero-BF16**. Risk high.
- Branch: `fea/eanble-reasoning-action-phase-5-session-3`.
- Last commit at start: `506d6a6` (AM-S2). This session's work is **uncommitted** (owner to review/commit).
- Status: **GATE-AM-S3-ACTION PASSES** (owner quality PASS — Feng, 2026-07-25). Action runs end to end on FP8 off
  the **quantized-only** checkpoint for all three v1-scope modes (agibotworld 29-D `forward_dynamics`/
  `policy`; av 9-D `inverse_dynamics`), served by the resident `vllm-omni` model via the video-API
  `action_mode`. `t2i` non-regressed (INV-2), CPU suite green, `openapi.json` unchanged (INV-8), no BF16 on
  the path (INV-4), residency safety net held (INV-5). Sharded review + adversarial verifier **PASS**.
  `OWNER-AM-ACTION-QUALITY` = **PASS** (Feng, 2026-07-25) → action is GPU-verified on FP8 (default-on stays AM-S4, INV-7).
- Changed files (this session):
  - **repo `api/`**: `engines/vllm_omni/work.py` (dispatch policy/ID; kind-aware conditioning cap),
    `engines/vllm_omni/client.py` (`action_resolved_params`/`build_action_form`/`action_extra_params_predict`/
    `run_action_job`), `engines/diffusers_action/loader.py` (retire the BF16 base default; graft dormant).
  - **repo `deploy`/env**: `.env.example` (retire the `COSMOS3_BASE_ACTION_DIR` BF16 default).
  - **repo `tests/`**: `test_vllm_omni_work.py` (+8 action tests; reworked unsupported-mode test),
    `test_action_loader_unit.py` (no-BF16-default + env-override tests).
  - **docs**: `docs/session_3/**` (brainstorming, design, execution_contract, decision_record,
    sharded_review, adversarial_verification, evidence/P1–P2); `docs/{evidence_map,risk_register,
    eval_seed_cases,model_setup,handoff}.md`.
- Checks run: `uv run pytest -m "not gpu"` green (exit 0); `uv run pytest tests/checkpoint_prep -q` green;
  `git diff --exit-code schemas/openapi.json` clean; `docker compose -f deploy/docker-compose.fp8.yml
  config` = no BF16 mount; **GPU-AM-ACTION-FP8** (P1 raw + P2 via the real `vllm_omni_work` wiring);
  **GPU-AM-T2I-NOREGRESS** (P2); sharded review + adversarial verifier (`docs/session_3/`).
- Checks NOT run: the **full-stack** api-container→orchestrator→omni action run (with the docker-socket
  start/stop + the Studio↔Action residency handling) as a single GPU run — I proved the api **code** path
  (`vllm_omni_work`) end to end against the live omni server, and the residency stays on `Plane.GENERATION`
  (one model), but the integrated container-driven run is the **AM-S4** all-modes smoke. NVFP4 action
  (AM-S5). The owner's `OWNER-AM-ACTION-QUALITY` signature.

## Narrative Context
AM-S1/S2 closed. AM-S3 enabled zero-BF16 action on FP8. The pivotal spike finding (a2): the resident
`vllm-omni` model **already serves all three action modes** via the diffusion **video-API `action_mode`**
(`forward_dynamics` = sync `/v1/videos/sync`; `policy`/`inverse_dynamics` = async `/v1/videos`, trajectory
in the completion body's top-level `action`) — NOT the openpi WS, which targets the *separate*
`nvidia/Cosmos3-Nano-Policy-DROID` checkpoint (this explained AM-S1's "Robot policy not available"). So
action needed **no new plane, no diffusers in-process, no fork change** — just api-side wiring in
`vllm_omni_work`/`client.py` (FD was already wired; add policy/ID) plus retiring the `COSMOS3_BASE_ACTION_DIR`
BF16 default. GPU-proven off the quantized-only checkpoint (peak 14.3 GiB, one resident model → Studio+Action
plane-merge). Owner trajectory-quality verdict: **PASS** (Feng, 2026-07-25) — action GPU-verified on FP8.

## Decision Log
| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| Action serving mechanism | **(a2)** omni video-API `action_mode` (resident model) | (a1) openpi WS; (c) diffusers in-process `Plane.ACTION` | (a1) is for the separate Policy-DROID checkpoint; (c) unneeded once (a2) was GPU-proven for all 3 modes | S-C, R-02, INV-5 |
| Checkpoint | reuse the deployed quantized FP8 (**no re-export**) | re-export/bundle adapters | E-06 refuted — adapters already bundled | E-06, R-01, NFR-5 |
| `(c)` `diffusers_action` graft | left **dormant**; retire its BF16 base default | fix its collision/`505`; delete it | owner chose a2-only; R-11 (not a required deletion) | R-11, INV-4 |
| Zero-BF16 action | `COSMOS3_BASE_ACTION_DIR` retired (no default → `None`) | keep the BF16 base default | INV-4 (no silent BF16) | INV-4 |
| Sharded-review #3 (loop dup) | **deferred** | refactor `run_video_job` now | avoid touching the proven t2v/i2v path at close-out | sharded_review §#3 |

## Next Priority Queue
1. **`OWNER-AM-ACTION-QUALITY` — DONE ✅ (Feng, 2026-07-25).** All three v1-scope modes judged good in the
   WebUI Action tab (agibotworld policy/FD 3D + rollout; av ID 2D plots) → action is **GPU-verified on
   FP8** (INV-6). **`GATE-AM-S3-ACTION` PASSES.** Default-on remains AM-S4 (INV-7).
2. **AM-S4 (default-on, FP8):** fold action into the clean default-on `make up-fp8` all-modes stack; run
   the **full-stack GPU smoke** incl. the api-container→orchestrator residency swaps (Studio↔Action merge
   + Reasoning swap); plus the inherited AM-S2 cleanups (commit/pin the `fengwang/vllm` fork; remove the
   legacy BF16 reasoning overlay + `WITH_REASONING` + dormant subprocess).
   - **BLOCKER found (AM-S3 owner run, 2026-07-25):** `make up-fp8` fails building
     `cosmos3-nano-vllm-reasoner:local` — the reasoner **build context ≠ COPY paths** mismatch:
     `deploy/docker-compose.fp8.yml` sets `build.context: ..` (repo root) but `deploy/vllm-reasoner.Dockerfile`
     does `COPY vllm-reasoner/patch/*.py` (resolves to `<root>/vllm-reasoner/…`, which doesn't exist — the
     files are under `<root>/deploy/vllm-reasoner/patch/`). AM-S2 built `:verify` manually with
     `context: deploy`; the compose rebuild (only triggered because `:local` is absent) breaks. **Fix in
     AM-S4** (out of AM-S3 scope — the reasoner Dockerfile is not in AM-S3's blast radius): prefix the COPYs
     with `deploy/`, or set `build.context: deploy`, or (per the AM-S2 plan) switch to a pinned public-fork
     install and drop the COPY-patch. Also causes the heavy omni+reasoner to both be created by `up -d`
     (VRAM contention risk) — part of the AM-S4 residency smoke.
3. **AM-S5 (NVFP4):** verify action on NVFP4 — the NVFP4 checkpoint also ships the `action_*` adapters, so
   the same video-API `action_mode` should extend; prove it on the 4-bit Blackwell kernels.

## Warnings And Gotchas
- Environment: action e2e needs the omni container up + the FP8 checkpoint mounted; use the shipped example
  assets as canonical inputs. ID takes a **video** (`video_path`); policy/FD take an **image** (`image_path`).
- `num_frames`/`action_chunk_size`: the omni pipeline requires `action_chunk_size == num_frames` or
  `num_frames-1`; `action_resolved_params` defaults `num_frames = chunk+1`. For ID, `chunk_size` should
  track the input video's frame count (av example: 61 frames → chunk 60).
- Known failing tests: none.
- **WebUI Action-tab "Run demo" (R-12): FIXED (owner-authorized amendment, 2026-07-25).** It used to send
  no conditioning (every mode 422'd). Now `demoActionBody(domain, mode)` auto-attaches the checkpoint's
  shipped example conditioning per mode (agibotworld first-frame image for policy/FD; av clip for ID), and
  the api trusts the read-only `assets/` mount via `COSMOS3_INPUT_ALLOWLIST` (compose). Files touched
  (out-of-default-scope, owner-OK): `webui/components/action-viewer/{demoBody.ts,ActionWorkspace.tsx}`,
  `deploy/docker-compose.base.yml`. Verified: demoBody.test (5), tsc, webui suite 218, CPU suite green,
  `openapi.json` unchanged. The in-container click-through is the AM-S4 smoke (mechanism P2-proven).
- **Backlog (owner-decided 2026-07-25, future development plan — NOT AM-S4/S5 scope):** an `av` **3D
  pose-path** viewer — render the vehicle's motion as a moving frame / ribbon in 3D (a trajectory viewer,
  distinct from the agibotworld URDF joint animator). Blocked on **documented av 9-D semantics** (which
  dims are translation / orientation / velocity — currently undocumented; the engine records only
  width=9). Until then `av` stays on the authoritative 2D plots by design (`viewerModeFor` fallback,
  `PROVENANCE.md`). When scheduled: author a candidate av pose-convention + a pose-path renderer, gated by
  the human visual gate like agibotworld.
- Deferred risk: sharded-review **#3** — `run_action_job` duplicates `run_video_job`'s poll/timeout loop; a
  future cleanup should extract a shared `_submit_and_poll(...)` (touches the proven video path — do it as
  a focused, test-guarded change, not at close-out).
- Files future sessions must not casually edit: `schemas/openapi.json` (INV-8); the proven `vllm-omni`
  image + `t2i` path (INV-2); `docs/archive/**`.

## Eval Seeds
- Missed check: none (the spike + sharded review caught the a1-vs-a2 surface and the untrusted-payload gap).
- New regression test candidate: `test_action_predict_empty_trajectory_fails_typed_no_artifact` (added).
- Instruction update candidates: **EV-AM-ACTION-SURFACE-IS-VIDEO-API** (find the model's *actual* serving
  path, not the first plausible-but-wrong surface); **EV-AM-UNTRUSTED-SERVER-PAYLOAD** (validate an
  engine/server response's shape + non-emptiness before persisting it). Both recorded in
  `docs/eval_seed_cases.md` (AM-S3 harvest).
