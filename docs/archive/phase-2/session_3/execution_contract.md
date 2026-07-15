# Session 3 Execution Contract - Joint Validation on RTX 5090

Date: 2026-07-09
Branch: `GPU-S3` (off `GPU-S2`)

## Planned File Changes

- **New:** `docs/session_3/**` (this planning pack; `probes/lib.py`,
  `probes/test_lib.py`, `probes/run_checkpoint_fetch.py`,
  `probes/run_direct_t2i.py`, `probes/run_fullstack_t2i.py`,
  `probes/run_t2v_smoke.py`, `probes/aggregate.py`, `probes/evidence*.json`,
  `probes/summary.md`).
- **Modified:** `docs/evidence_map.md`, `docs/eval_seed_cases.md`,
  `docs/model_setup.md`, `docs/release_checklist.md`, `README.md`,
  `docs/risk_register.md`, `docs/handoff.md`.
- **Not modified:** `api/**`, `webui/**`, `deploy/vllm-omni.Dockerfile`,
  `deploy/docker-compose*.yml`, `schemas/**`, `.github/**`, any external
  `wfen/*` HF repo. (Compose YAML is not in the contract's
  `blast_radius.allowed_files` list either, so it is treated as forbidden by
  the same "only touch what's explicitly listed" reading applied to
  `tests/**` in brainstorming — direct-generation calls run via `docker
  compose exec` instead of a compose file edit; see `plan.md`.)
- **Local, gitignored, not committed:** `models/Cosmos3-Nano-{FP8,NVFP4}
  -Blockwise` (checkpoint weights — `.gitignore` line 28 / INV-2).

## Allowed Blast Radius

Exactly `session_3_contract.yaml`'s `blast_radius.allowed_files`:
`docs/session_3/**`, `docs/model_setup.md`, `docs/release_checklist.md`,
`README.md`, `docs/evidence_map.md`, `docs/risk_register.md`,
`docs/eval_seed_cases.md`, `docs/handoff.md`. Anything else requires
stopping and recording a contract amendment first (matching `GPU-S1`'s
`A1`/`GPU-S2`'s `A1`-`A3` precedent), not a silent edit.

## First Test to Write

`docs/session_3/probes/test_lib.py::test_check_no_lfs_pointers_flags_a_pointer_file`
— written and run (`uv run pytest docs/session_3/probes/test_lib.py -v`)
before `lib.py` exists, so it fails on import first, per Task 2 in `plan.md`.

## Checks to Run After Each Task

- After Task 2 (probe library): `uv run pytest
  docs/session_3/probes/test_lib.py -v` — all green, no GPU/network.
- After Task 3 (T1): re-list the downloaded directory and re-run
  `check_no_lfs_pointers`/`check_no_stale_index` against it independently of
  the probe's own internal call (a second, separate look, matching
  `GPU-S2`'s "independent re-run" adversarial-verification lesson).
- After Tasks 5/6 (T3-T6): `curl -sf http://localhost:8000/v1/models`
  against the live stack before each generation call; confirm the written
  evidence fragment's `verdict` field before moving to the next checkpoint.
- After Task 7 (T7): confirm `evidence_t2v_smoke.json` exists and its
  `verdict` is one of `PASS`/`FAIL`/`SCOPED_OUT` (never absent, never a bare
  crash) regardless of outcome.
- After Task 8: `rg --hidden --glob '!.git' "GPU-unverified|4e181f99|
  b5c9332e"` sweep across the modified docs, to catch a missed per-mode
  marking or a reintroduced pre-fix revision — using `--hidden`, per
  `GPU-S2`'s own harvested lesson (`EV-GPU-SWEEP-HIDDEN-FILES`).
- `make scan` (weight-copy + private-ref scan) before any commit.

## Review Axes

Full 5-axis sharded review (risk_level: high, per `session_3_contract.yaml`):
correctness, security, tests, architecture, performance.

## Adversarial Verifier Brief

Falsify the claim that `GATE-GPU-S3-VALIDATION` passes. Specifically check:

- Was the checkpoint fetch a genuinely fresh download (new `models/`
  directory, not a symlink or copy of a pre-existing `/data/models/
  Cosmos3-Nano-*` directory)?
- Does every evidence record actually carry all INV-8 fields (hardware,
  driver/CUDA, checkpoint repo+revision, vLLM-Omni commit
  `697035018b70cef76b974a909d23371a9984c3f2`, request shape, artifact
  metadata, pass/fail)?
- Is any T2I `PASS` claim unsupported by a real artifact file /
  `evidence_map.md` row?
- Is the T2V outcome recorded (pass, fail, or scoped-out-with-reason), or
  silently dropped?
- Did a per-mode marking upgrade to "T2I-verified" for a checkpoint whose
  evidence is actually `FAIL`?
- Did any step use a manual index-removal or LFS-pointer workaround?
- Re-run the hidden-file-aware sweep independently rather than trusting the
  session's own sweep output.

## Done Condition

`GATE-GPU-S3-VALIDATION` passes: FP8 and NVFP4 T2I are proven end to end
(direct and full-stack) against the fresh `GPU-S2`-revision checkpoints and
the `GPU-S1` image, with no manual workaround; the T2V attempt is recorded
either way (pass, fail, or scoped out with a reason); every evidence record
carries the full INV-8 field set; `docs/evidence_map.md`,
`docs/eval_seed_cases.md`, `docs/model_setup.md`, `docs/release_checklist.md`,
`README.md`, and `docs/risk_register.md` are consistent with that evidence;
sharded review and adversarial verification both complete with no
unresolved Critical/High finding; `docs/handoff.md` is updated.

**Human gate (per `project_contract.md` §5):** fires on a T2I failure
(either checkpoint, direct or full-stack) or a drift-D1 recurrence — the
owner is brought in before deciding retry vs. investigate vs.
accept-as-limitation. A T2V failure does not trigger the gate; it is
recorded and reported, not blocking.
