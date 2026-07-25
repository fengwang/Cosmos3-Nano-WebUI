# AM-S3 Execution Contract — Action on FP8 via omni video-API (a2), zero-BF16

Date: 2026-07-25 · Session: AM-S3 · Gate: `GATE-AM-S3-ACTION`. Mechanism fixed by the spike (`evidence/P1`):
**(a2)** — the resident omni model serves all three action modes via the video-API `action_mode`. FD is
already wired; this session wires **policy + inverse_dynamics** and enforces **zero-BF16**.

## Planned file changes (as-built)
1. `api/engines/vllm_omni/client.py` — add pure `action_resolved_params(record)` (policy/ID form + meta
   source; derives `raw_action_dim` from the embodiment via `preprocessing.action_schema.raw_action_dim_of`),
   `build_action_form(record, *, input_reference)`, and `run_action_job(record, report, *, transport,
   input_reference)` (async submit → poll → read top-level `action`; download rollout bytes only when the
   server returns a video, i.e. policy; ID is `action_only`).
2. `api/engines/vllm_omni/work.py` — add `policy`, `inverse_dynamics` to `_SUPPORTED_MODES`; dispatch them
   through `run_action_job`; write artifacts matching the existing job contract (INV-8):
   - `inverse_dynamics` → artifact = trajectory JSON (`artifacts.write_trajectory_json(action.data, id)`),
     **no** `meta.trajectory_path` (the artifact *is* the trajectory — mirrors `gen_worker._encode_action_reply`).
   - `policy` → artifact = rollout MP4 (`artifacts.write_video_bytes`), `meta.trajectory_path` = trajectory JSON sidecar.
   - conditioning: policy needs `image_path`; ID needs `video_path` (typed `invalid_input` + no submit if missing);
     the video part uses the video byte cap (not the image cap).
3. `api/engines/diffusers_action/loader.py` — retire the `COSMOS3_BASE_ACTION_DIR` BF16 default (INV-4):
   drop `DEFAULT_BASE_ACTION_DIR`/`from_env` reliance on a BF16 base so nothing defaults to BF16. The
   dormant `(c)` graft is otherwise left in place (R-11).
4. `.env.example` — drop the BF16 `COSMOS3_BASE_ACTION_DIR` default; note action is served by the resident
   omni model (no BF16 base).
5. `deploy/docker-compose.{base,fp8}.yml` — confirm/ensure **no** BF16 base mount for action (assert via
   `docker compose … config`). (Likely already true — action rides `vllm-omni`.)
6. `docs/model_setup.md` — record: action served off the quantized-only FP8 checkpoint via the omni video
   API; `COSMOS3_BASE_ACTION_DIR` retired; per-mode matrix updated. **No re-export / new revision** (E-06 refuted).
7. `tests/**` — new omni-work policy/ID tests; update `test_unsupported_mode_raises_no_submit` (ID now
   supported → use a genuinely unknown mode); update `test_action_loader_unit` base-dir assertion (R-11).
8. `docs/session_3/**`, `docs/{evidence_map,risk_register,eval_seed_cases,handoff}.md` — close-out.

## Allowed blast radius
Per `session_3_contract.yaml` `blast_radius.allowed_files`. All planned edits fall inside it
(`api/engines/vllm_omni/**`, `api/engines/diffusers_action/**`, `.env.example`, `deploy/**`,
`docs/**`, `tests/**`). **Not touched:** `schemas/openapi.json` (INV-8), `api/jobs/**` (only *called*),
`api/app/routes/reasoning.py`/`api/engines/vllm/**` (AM-S2), `docker-compose.nvfp4.yml` (AM-S5),
`webui/**`, `README.md`, `docs/walkthrough.md`, `docs/archive/**`, the omni fork (no fork change).
**No new `Plane.ACTION`** — action stays on `Plane.GENERATION` (Studio+Action plane-merge; INV-3/INV-5).

## First test (spec-derived)
`tests/test_vllm_omni_work.py::test_inverse_dynamics_async_writes_trajectory_json` — a fake transport
whose poll body carries `action={data,shape,...}`; assert `vllm_omni_work(_id_rec(video_path=…))` submits
async (`post` to `/v1/videos`), reads the `action`, writes a `.json` trajectory artifact, and records
`meta.action_mode == "inverse_dynamics"` — with **no** `trajectory_path` (artifact is the trajectory).

## Checks after each task (targeted)
- `uv run pytest tests/test_vllm_omni_work.py -q` (adapter unit)
- `uv run pytest tests/test_action_loader_unit.py tests/api/test_routes_action.py -q` (graft/route)
- `uv run pytest -m "not gpu" -q` (full CPU suite) before closing
- `git diff --exit-code schemas/openapi.json` (INV-8) + `uv run pytest tests/checkpoint_prep -q`
- `rg -n "COSMOS3_BASE_ACTION_DIR" api/ deploy/ .env.example` (zero-BF16 sweep — no BF16 default remains)
- GPU (agent-driven): action e2e (FD/policy/ID via the api→omni path) + `t2i` non-regression smoke;
  `docker compose -f deploy/docker-compose.fp8.yml config` shows no BF16 mount.

## Review axes (end)
correctness, security, tests, architecture, performance, readability (sharded, fresh-context subagents).

## Adversarial verifier brief
Falsify the done condition. Attack: (1) action still reads `action_*`/`COSMOS3_BASE_ACTION_DIR` from a
BF16 base (INV-4) — grep the path + `docker compose config`; (2) `openapi.json` shape changed (INV-8);
(3) `t2i` regressed / not re-run at the checkpoint (INV-2); (4) a mode marked verified with no owner
quality PASS (INV-6); (5) ID/policy artifact/trajectory contract diverged from the `gen_worker` shape the
webui targets; (6) a new plane / co-residency claim without a VRAM trace (INV-5); (7) partial artifact on
failure. All must be refuted with evidence.

## Done condition (`GATE-AM-S3-ACTION`)
Action runs e2e on FP8 off the quantized-only checkpoint for the v1 embodiments (agibotworld FD/policy;
av ID) via the resident omni model; `t2i` smoke re-passes (INV-2); CPU suite green; `openapi.json`
unchanged (INV-8); no BF16 on the action path (INV-4); residency safety net intact (INV-5); owner
`OWNER-AM-ACTION-QUALITY` recorded **PASS** (INV-6; Feng, 2026-07-25). No
checkpoint re-export (E-06 refuted); if `integrity_probe` ever fails on the pinned revision, the NFR-5
re-pin path triggers (not expected).
