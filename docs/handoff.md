# Session Handoff

## State Snapshot
- Session: `LX-S1` — Idle Keep-Warm 10 min → 30 min (`GATE-LX-S1-TIMEOUT`).
- Branch: `fea/doc-adhd-optimization`.
- Last commit: `c6300d1` (phase-4 blueprint). **LX-S1 changes are in the working tree, uncommitted.**
- Changed files:
  - `api/app/main.py` — idle env fallback `"600"→"1800"` (+ rationale comment).
  - `api/orchestrator/manager.py` — `Orchestrator` ctor default `600.0→1800.0`.
  - `.env.example` — new "Single-GPU comfort: idle keep-warm" section (`COSMOS3_IDLE_TIMEOUT_SECONDS=1800`).
  - `tests/test_idle_keepwarm_default.py` (new) — app-wired 1800 + override + 0 + constructor default + 0-schedules-no-timer.
  - `docs/evidence_map.md` — "LX-S1 execution audit" (gen/cold-start ≥30 min, unchanged).
  - `docs/archive/phase-3/session_4/plan.md` — **authorized** one-line path scrub (§2.1).
  - `docs/session_1/**` (refining, execution_contract, sharded_review, adversarial_verification), `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/handoff.md`.
- Checks run: `uv run pytest -m "not gpu"` → **523 passed, 0 failed**; `ruff check` on changed files → clean; `rg` deterministic checks → 1800 at both sources + `.env.example`; `uv run python tests/test_private_ref_scan.py` → clean; independent 6-axis review → no Critical/High; fresh-context adversarial verifier → **PASS** (tamper-tested).
- Checks not run: GPU smoke (not required this phase; `MIG-S8` remains the standing manual gate); WebUI `pnpm build/lint/typecheck/test` (no non-doc WebUI file touched); no static type-check gate (project gates on ruff + pytest — pre-existing Pyright hints on `main.py`'s `MeteredOrchestrator` assignment are not part of the gate and were not introduced here).
- Current status: **`GATE-LX-S1-TIMEOUT` satisfied by the diff; awaiting a commit decision.**

## Narrative Context
Raised the idle keep-warm default `600→1800 s` at both sources of truth (the `main.py` env fallback
and the `Orchestrator` constructor) so a single RTX 5090 keeps the resident plane warm across a
normal generate→watch→think→tweak pause instead of paying a cold reload. Surfaced the knob in
`.env.example`, and proved the behavior with a CPU test that pins the **app-wired** value (through
`create_app()`, not a literal) plus the override, `0`-disabled, and constructor-default cases. The
generation-duration (2400/7200 s) and cold-start (1800 s) ceilings were audited as already ≥30 min
and left unchanged. A pre-existing leaked `/workspace/<name>` path in an archived doc — which was
failing the private-ref scan — was scrubbed under an owner-authorized, one-line exception so the CPU
suite is genuinely green. No other timeout, schema, route, or `README.md` was changed.

## Decision Log
| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| Change scope | both sources + wiring test | only `main.py` | avoid two-source drift | FR-1, E-06/R-02 |
| Test target | app-wired value via `create_app()` | module literal/constant | catch a `main.py` wiring regression | adversarial_cases |
| `.env.example` form | active line = code default + comment | commented-out only | "default settings = code default", edit-free; matches the "shown for clarity" block | FR-3, PRD Dec.4 |
| Ceremony | proportionate (`refining.md` + `execution_contract.md`) | full 7-doc pipeline | low-risk 2-line change; spec already precise | owner decision 2026-07-24 |
| Pre-existing archive scan leak | scrub to U+2026 ellipsis (authorized) | leave red / weaken scanner | fixes a real INV-1 leak; green suite; minimal, matches existing practice | owner decision; exec_contract §2.1 |

## Next Priority Queue
1. **`LX-S2` (ADHD README rewrite).** The idle keep-warm default is now **1800 s (30 min)** — the Status & security callout MUST state this behavior (R-03/R-04). `README.md` is `LX-S2`'s exclusive surface; it was not touched here (R-05 honored).
2. **Commit the `LX-S1` change** (currently uncommitted) at a clean checkpoint.
3. (Future, non-goal here) collapse the two idle-default definitions into a single source of truth.

## Warnings And Gotchas
- Environment issues: none. `transformers` is absent on the host → the edge tokenizer degrades to `None` (expected, harmless; not GPU-related).
- Known failing tests: none now. The previously-failing private-ref scan (archived workspace path) is fixed.
- Deferred risks: the WebUI SSE `heartbeatTimeoutMs` (30 s liveness, **E-08/R-03**) is deliberately **out of scope** — a genuinely-quiet long job could still drop in the browser; that is separate from idle keep-warm. Longer keep-warm holds VRAM for 30 min (intended on the single-user 5090; `acquire` evicts-before-load, so no starvation — INV-4/E-05).
- Files future sessions must not casually edit: `docs/archive/**` — the `LX-S1` scrub was a **bounded, owner-authorized, one-line exception**, NOT a general license to edit archives; `README.md` (owned by `LX-S2`); the other-timeout files (`api/jobs/gen_client.py`, `api/engines/vllm_omni/work.py`, `api/app/routes/reasoning.py`) are audit-only.
- Governance note: if project policy forbids any archive edit, revert that one line and instead either exclude `docs/archive/**` from the scanner or track the leak as a separate known issue — but then the CPU suite shows that one pre-existing failure again.

## Eval Seeds
- Missed check: none. The scanner already covered `docs/archive/**`; the baseline run caught the leak *before* editing (procedure worked).
- New regression test candidate: `EV-LX-ARCHIVE-SCRUB-ELLIPSIS` (recorded in `docs/eval_seed_cases.md`) — a `/workspace/…` redaction must use the single char U+2026, not `...` (ASCII dots still match the scanner's char class).
- Instruction update candidate: add a scrub-practice note that ellipsis redaction requires U+2026; reuse the "assert the app-wired value, not a literal" pattern for future default-value changes.
