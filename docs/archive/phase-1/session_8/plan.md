# Session 8 Plan - Release Gate, Evidence Review, and Handoff

Session: MIG-S8 · Risk: high · Gate: `GATE-MIG-S8-BETA`
Input: `tasks.md`, `specs/*.md`, `design.md`. Docs-only blast radius; no runtime edit.

"TDD" here = for each check, state the expected result first, run it, then record the raw
output as the evidence. For each doc deliverable, the "test" is a completeness/consistency
assertion derived from its spec scenarios.

## Task 1.3 — finish the refining pack

Write `execution_contract.md` (this pack's last piece). Commit point:
`docs(s8): refining pack (brainstorm/proposal/design/specs/tasks/plan/exec-contract)`.

## Task 2 — deterministic checks

Run from repo root (via `rtk`; commands are read-only / render-only):

```bash
rtk git status --short --branch
# expect: branch session-8, clean (or only docs/session_8 additions staged)

uv sync --frozen --group test-cpu
uv run ruff check api tests          # expect: 0 issues
uv run pytest -m "not gpu" -q        # expect: pass, record count (S7 baseline: 485)

cd webui && pnpm install --frozen-lockfile && pnpm build && pnpm lint && pnpm typecheck && pnpm test
# expect: all pass; record Vitest count (S7 baseline: 209); cd back

docker compose -f deploy/docker-compose.fp8.yml config   # expect: exit 0, empty stderr
docker compose -f deploy/docker-compose.nvfp4.yml config  # expect: exit 0, empty stderr

uv run python tests/test_private_ref_scan.py             # expect: 0 findings
git ls-files | rg -i "\.(safetensors|pt|pth|ckpt|mp4|mov|avi|webm)$"  # expect: empty
```

Notes to record in `deterministic_checks.md`:
- `$PRIVATE_REF_PATTERN` is unset → ENVIRONMENT; the committed scanner + a documented
  fallback `rg` are authoritative (S1/S5 precedent).
- The GitHub-hosted Actions run is not executed locally (nothing pushed) → at-publish item.
- Any FAIL → write `failure_arbiter.md` (category + evidence + allowed/forbidden action)
  before any edit; no runtime-source fix without owner approval.

Commit point: `docs(s8): deterministic checks log (CPU checks re-run)`.

## Task 3 — acceptance matrix, evidence review, gate record

- 3.1 `outputs/acceptance_matrix.md`: enumerate FR-1..FR-12 (+ NFR-1..NFR-6) from
  `docs/prd.md` §4; for each MUST write gate + public evidence pointer + verdict. Self-test:
  every MUST-keyword requirement has exactly one row; every `PASS` cites public evidence;
  FR-9/NFR-6 are `BETA-LIMITED` with the deferred command.
- 3.2 `outputs/evidence_review.md`: one row per major claim → public evidence pointer; tag
  verified-now vs manual-gate-deferred. Self-test: `tests/test_private_ref_scan.py` clean
  over `docs/session_8/**`; every row has a pointer or a speculative/deferred tag.
- 3.3 `outputs/gate_record.md`: `GATE-MIG-S1..S8` rows; GPU NOT-YET-RUN + pin/revisions;
  drift D1 limitation; recommended `GATE-MIG-S8-BETA` verdict + rule + "owner ratifies".

Commit point: `docs(s8): acceptance matrix + evidence review + gate record`.

## Task 4 — reconciliation

- 4.1 `docs/evidence_map.md`: append an `MIG-S8` row (release-gate review, checks re-run,
  manual-gate deferral) — public evidence only.
- 4.2 `docs/risk_register.md`: update R-05 (GPU), R-08 (surface breadth), R-13 (fork image),
  R-16 (socket) with the owner beta-limited disposition + owning follow-up; confirm no
  release-blocking risk is open without an owner decision.
- 4.3 `docs/eval_seed_cases.md`: mark deterministic cases satisfied through S7; record each
  `EV-MIG-GPU-*` as the S8 manual gate.
- 4.4 `docs/release_checklist.md`: tick §1–§6/§8 items verified this session with evidence;
  keep §7 (GPU) and §9 (at-publish) as manual gates.

Self-test: re-run `tests/test_private_ref_scan.py` over the edited docs (0 findings);
cross-check no contradiction with the README claim matrix / `docs/model_setup.md`.

Commit point: `docs(s8): reconcile evidence/risk/eval/checklist to final beta state`.

## Task 5 — review gates

- 5.1 Dispatch 5 read-only reviewer subagents (correctness/security/tests/architecture/
  performance) over `git diff main...session-8 -- docs/` + the outputs. Require each to cite
  file/line evidence and >0 tool uses; reject rubber-stamps. Write `sharded_review.md`.
- 5.2 Fix only High/Critical (doc/evidence errors). Re-run the affected check. Iterate ≤3;
  if the same failure repeats twice, invoke the Failure Arbiter.
- 5.3 Dispatch the fresh-context adversarial verifier (sees only session contract, project
  contract, diff, evidence). Falsify the done condition + the GO recommendation against the
  4 adversarial cases + the failure modes. Write `adversarial_verification.md`.

Commit point: `review(s8): sharded review (5 axes) + fixes; adversarial verification`.

## Task 6 — close-out

- 6.1 Re-run the contract's final checks; confirm the done condition clause by clause.
- 6.2 Write `docs/handoff.md` from the template (state, narrative, decision log, next queue,
  warnings, GPU summary, pin/revisions, recommended GO/NO-GO for ratification).
- 6.3 Add `docs/eval_corpus/mig_s8_*.md` seeds for anything caught/missed.
- 6.4 Present the recommended verdict + evidence bundle to the owner.

Commit point: `docs(s8): handoff + eval seeds + recommended GO/NO-GO (owner ratifies)`.
