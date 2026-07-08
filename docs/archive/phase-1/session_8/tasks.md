# Session 8 Tasks - Release Gate, Evidence Review, and Handoff

Session: MIG-S8 · Risk: high · Gate: `GATE-MIG-S8-BETA`
Ordered by dependency. Each task is verifiable. Docs-only blast radius.

## 1. Refining pack

- [x] 1.1 Write `brainstorming.md`, `proposal.md`, `design.md`.
- [x] 1.2 Write `specs/*.md` (deterministic-checks, acceptance-matrix, evidence-review,
      gate-record, gpu-beta-limited-disposition, doc-reconciliation).
- [ ] 1.3 Write `tasks.md`, `plan.md`, `execution_contract.md`.

## 2. Deterministic checks (evidence of record)

- [ ] 2.1 Run `rtk git status --short --branch`; record clean tree + branch.
- [ ] 2.2 Run the torch-free Python suite (`uv sync --frozen --group test-cpu`,
      `uv run pytest -m "not gpu"`, `ruff check api tests`); record counts.
- [ ] 2.3 Run WebUI `pnpm build`→`lint`→`typecheck`→`test`; record Vitest count.
- [ ] 2.4 Run `docker compose config` for fp8 + nvfp4; record exit 0 / no unset-var warning.
- [ ] 2.5 Run the committed private-reference scan + weight/media file-path scan; record 0
      findings; note `$PRIVATE_REF_PATTERN` unset as ENVIRONMENT.
- [ ] 2.6 Write `outputs/deterministic_checks.md` (command → result → verdict; checks not
      run recorded with reason). Classify any failure via Failure Arbiter first.

## 3. Acceptance and evidence

- [ ] 3.1 Write `outputs/acceptance_matrix.md` — one row per PRD MUST → gate → public
      evidence → verdict `{PASS|BETA-LIMITED|NO-GO}`.
- [ ] 3.2 Write `outputs/evidence_review.md` — each major claim → public evidence row;
      verified-now vs manual-gate-deferred; no private citation.
- [ ] 3.3 Write `outputs/gate_record.md` — `GATE-MIG-S1..S8` status + evidence; GPU
      manual-gate status + pin/revisions; drift D1 limitation; recommended verdict + rule.

## 4. Reconciliation

- [ ] 4.1 Update `docs/evidence_map.md` (add the `MIG-S8` row).
- [ ] 4.2 Update `docs/risk_register.md` (no unowned release blocker; record GPU-deferral
      decision on R-05/R-08/R-13; final R-16 disposition).
- [ ] 4.3 Update `docs/eval_seed_cases.md` (mark satisfied evals; GPU cases = S8 manual gate).
- [ ] 4.4 Update `docs/release_checklist.md` (tick verified items with evidence; leave GPU +
      at-publish as manual gates).

## 5. Review gates (high risk)

- [ ] 5.1 Sharded review — 5 read-only reviewer axes over deliverables + diff; dedup; treat
      output as untrusted; write `sharded_review.md`.
- [ ] 5.2 Fix only High/Critical findings (doc/evidence errors); re-run affected checks.
- [ ] 5.3 Adversarial verification — fresh context vs contract + diff + evidence; write
      `adversarial_verification.md`; classify any FAIL via Failure Arbiter.

## 6. Close-out

- [ ] 6.1 Re-run final contract checks; verify the done condition.
- [ ] 6.2 Write/update `docs/handoff.md` (state, decision log, next queue, warnings, GPU
      summary, pin/revisions, recommended GO/NO-GO for owner ratification).
- [ ] 6.3 Add `docs/eval_corpus/mig_s8_*.md` eval seeds.
- [ ] 6.4 Present the recommended verdict + evidence bundle to the owner for ratification.
