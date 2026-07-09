# Session Handoff

## State Snapshot
- Session: `GPU-S3` — Joint Validation on RTX 5090
- Branch: `GPU-S3` (off `GPU-S2`; `GPU-S1`/`GPU-S2` still not merged into `phase-2`)
- Last commit: `7bfc4ad` at the time this handoff was drafted (a final eval-seed/handoff
  commit follows immediately after)
- Changed files: `docs/session_3/**` (new: planning pack, probe scripts, evidence,
  sharded review, failure arbiter, adversarial verification), `README.md`,
  `docs/evidence_map.md`, `docs/eval_seed_cases.md`, `docs/model_setup.md`,
  `docs/release_checklist.md`, `docs/risk_register.md`, `docs/handoff.md` — exactly
  `session_3_contract.yaml`'s allowed blast radius; no touches to `api/**`, `webui/**`,
  `deploy/vllm-omni.Dockerfile`, `schemas/**`, or `.github/**`.
- Checks run: `uv run pytest docs/session_3/probes/test_lib.py -v` (30/30 passing);
  `make scan` (weight-copy + private-reference, clean — re-run after every commit from
  partway through the session onward, following a lesson this session itself had to
  learn three times); live `docker compose config` mount-resolution checks (both with and
  without the session's env override); live GPU execution for every task (T1 checkpoint
  fetch ×2, T3/T4 direct T2I ×2, T5/T6 full-stack T2I ×2, T7 T2V smoke — all PASS, each
  independently spot-checked with `file`/`ffprobe`/manual weight-file inspection beyond
  the probes' own self-report); sharded review (5 axes); adversarial verification (3
  rounds, converged on round 3).
- Checks not run: anything in `GPU-S4`/`GPU-S5` scope (upstream `vllm-omni` state,
  `precheck-pr`, CI); inspecting the generated artifacts' actual pixel/frame content
  beyond hash + `file`/`ffprobe` validity (binaries correctly not committed, per
  INV-1/§6).
- Current status: **`GATE-GPU-S3-VALIDATION` passes.** FP8 and NVFP4 T2I proven end to
  end (direct and full-stack) against the fresh `GPU-S2`-revision checkpoints through the
  unmodified `GPU-S1` image, no manual workaround; a best-effort NVFP4 T2V smoke passed on
  the first attempt. `R-05` and `R-09` closed. `R-10` stays open (out of scope, owner
  decision). A new risk, `R-11`, opened and left open — real, but outside this session's
  blast radius to fix.

## Narrative Context
This session proved the combined claim `GPU-S1` and `GPU-S2` each left open on their
own: a fresh operator following only the README gets a working, from-source,
publicly-checkpointed T2I deployment. It found and fixed one critical bug along the way
that would have invalidated the whole result: every generation probe was silently
mounting a stale, pre-fix, manually-patched local checkpoint instead of the fresh
download, because this repo's own `.env` convenience pin outranked the compose file's own
default — caught by sharded review, not by this session's own Task-Loop self-critique.
Adversarial verification then needed three rounds to converge, surfacing two further real
gaps (an evidence-provenance claim that turned out unprovable from git history alone, and
a sharp edge where the contract's own literal reproduction command still silently uses the
stale checkpoint) and, less happily, the exact same private-reference-scan regression
recurring three separate times as later commits kept describing the earlier fixes. Every
`GPU-S3`-owned finding is now fixed and re-verified live; the two that aren't (`R-11`, and
whether to clean up this branch's local git history before it's ever pushed or merged) are
outside this session's authority and are handed off explicitly below rather than silently
dropped.

## Decision Log
| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| R-10 (guardrails-on) scope | Out of scope this session | Best-effort stretch; required this session | Owner decision — `session_3.md`'s in-scope list and `GATE-GPU-S3-VALIDATION`'s own text are both silent on guardrails | `docs/session_3/brainstorming.md` |
| Probe tooling shape | Small focused probes + a pure aggregator | One end-to-end orchestrator; shell-only runbook | Isolates failure blast radius per task; matches the Task Loop's one-task-at-a-time checkpoints | `docs/session_3/design.md` D1 |
| Checkpoint-mount bug fix | Explicit `env=` override in `compose_lifecycle.bring_up()` + a preflight that fails loudly on any mismatch | Edit `.env` or the compose files directly | Both outside `GPU-S3`'s blast radius; the override is verified live to outrank `--env-file`'s value | `docs/session_3/probes/compose_lifecycle.py`, commit `0fc75de` |
| Evidence provenance | Added a required `run_at` ISO-8601 timestamp to every `EvidenceRecord` | Leave re-run claims as unverifiable prose | Adversarial verification round 1: "re-ran, same result" was indistinguishable from "never re-ran" without it | `docs/session_3/probes/lib.py`, commit `4317245` |
| API-key testing | Session-defined test key injected via `extra_env`, never `.env`'s own value | Parse `.env`'s `COSMOS3_API_KEY` line as before | That line is genuinely empty; a naive parser (this session's own first attempt) and Docker Compose's own `.env` parsing both misread its trailing inline comment as the value, so the two happened to "match" by parser-bug coincidence, not real auth | `docs/session_3/probes/run_fullstack_t2i.py`, commit `0fc75de` |
| Byte-identical framing | Dropped — per-artifact validity is the property that matters | Cite hash-equality across direct/full-stack as a confirmed invariant | This session's own re-runs disproved it: the same checkpoint+prompt+seed produces a different hash on a different run (GPU kernel execution-order variance) | `docs/evidence_map.md`, commit `916cc84` |

## Next Priority Queue
1. **`GPU-S4`** (upstream state and isolation) — the next session per `project_contract.md`
   §5's routing table; no dependency on anything unresolved in `GPU-S3`.
2. **`R-11` disposition** — **partially closed** (amendment `GPU-S3-A1`, owner go-ahead):
   `.env.example` now warns explicitly at `COSMOS3_FP8_DIR`/`COSMOS3_NVFP4_DIR` about this
   exact failure mode and names the `docker compose config` check to run first. Residual:
   `session_3_contract.yaml`'s/`docs/session_3.md`'s own literal `deterministic_checks`
   text is unchanged (still outside blast radius), and this host's actual `.env` was
   already customized before this warning existed — a future session should still verify
   the resolved mount explicitly rather than assume the warning was heeded.
3. **Local git history**: commits `fa81e11` through `ac11cb3` on this branch contain a
   private absolute host path (the session's scratchpad path, this repo's own checkout
   path) in `constants.py`/evidence fragments — fixed at `be59188`, but still reachable in
   those earlier commits. The branch has not been pushed anywhere. Recommend squashing or
   rebasing this branch's history before any push or non-squash merge — deliberately not
   done automatically by this session, since rewriting history is a destructive operation
   that needs explicit owner authorization, not a unilateral agent decision.
4. **`R-10`** (guardrails-on path) — needs gated `nvidia/Cosmos-1.0-Guardrail` model access
   and `HF_TOKEN` provisioned in a session with GPU access; still unverified.
5. Medium/Low findings deferred from this session's sharded review (see
   `docs/session_3/sharded_review.md`'s "Medium"/"Low" sections) — mostly small
   architecture/test-coverage items (duplicated polling helpers across scripts,
   `REPO_ROOT` computed identically in six places, a few extractable-but-untested pure
   fragments inside Action scripts) reasonable for a future hardening pass, not urgent.

## Warnings And Gotchas
- **Environment issues:** none blocking. RTX 5090, Docker, Compose, and HF auth (as
  `wfen`) all functional; `/workspace` has ample disk headroom (checked: 1.2 TB free).
- **Known failing tests:** none — 30/30 passing at handoff time.
- **Deferred risks:** `R-10` (guardrails-on unverified), `R-11` (the contract's own bare
  `deterministic_checks` command silently mounts a stale checkpoint unless routed through
  `docs/session_3/probes/compose_lifecycle.py`'s override).
- **Files future sessions must not casually edit:** the same forbidden set as `GPU-S3`
  (`api/**`, `webui/**`, `deploy/vllm-omni.Dockerfile`, `schemas/**`, `.github/**`), plus
  the perennial `docs/archive/phase-1/**` (historical, never edited post-archive).
- **Stale local checkpoint copies:** `/data/models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise` on
  this host are still at the pre-`GPU-S2` revisions with a manually-applied index-removal
  workaround (`model.safetensors.index.json.stale-bak`) and at least one unresolved LFS
  pointer (`BIAS.md`). They are also exactly what `.env`'s `COSMOS3_FP8_DIR`/
  `COSMOS3_NVFP4_DIR` point at. Do not treat a bare `docker compose up` against this repo's
  compose files as using a fresh checkpoint — see `R-11`.
- **Generation is not bit-deterministic run to run**, even with a fixed seed — expect a
  different artifact hash across independent runs of the same checkpoint/prompt/seed.
  Validity (does it decode as a well-formed image/video at the requested shape), not hash
  equality, is the property any future session should actually check.

## Eval Seeds
- Missed check: this session's own Task-Loop self-critique (3 generate-critique-fix
  cycles per affected script) never caught the checkpoint-mount bug — only sharded review
  did. See `docs/eval_seed_cases.md`'s new `EV-GPU-COMPOSE-ENV-PIN-OVERRIDE`.
- New regression test candidate: `EV-GPU-EVIDENCE-PROVENANCE-TIMESTAMP` and
  `EV-GPU-SCAN-AFTER-EVERY-COMMIT` (the latter recurred three separate times in this
  session alone) and `EV-GPU-NO-UNIFORM-GENERALIZATION` — all added to
  `docs/eval_seed_cases.md`'s "GPU-S3 Retrospective Additions".
- Instruction update candidate: session contracts' `deterministic_checks` blocks should
  name required env-var overrides explicitly wherever a local `.env` convenience default
  could otherwise substitute a stale path (`R-11`) — no session currently has the
  authority to make that edit from within its own blast radius, which is itself worth the
  next blueprint revision's attention.
