# Session 5 Failure Arbiter - CPU-Only CI and Test Stabilization

Session: MIG-S5

Every check failure is classified before any fix (BUG / SPEC_GAP / AMBIGUITY /
ENVIRONMENT / TEST_BUG). Reference: `docs/agent_workflow/prompts/failure_arbiter.md`.

## FA-1 — Private-reference scan matched prior-session scrub documentation

- **Symptom:** `tests/test_private_ref_scan.py::test_clean_tree_has_no_findings`
  failed with 4 findings, all `[private_mount] /data/home` in
  `docs/session_3/{plan,scrub_report}.md` and
  `docs/session_4/{plan,execution_contract}.md`.
- **Evidence:** each hit is `/data/home` used **as a documented regex / `rg`
  pattern**, e.g. `-e '/data/home'` in the S4 provenance-regression command and
  `/data/home_[^/]+` in the S3 scrub-pattern list — not a real filesystem path.
- **Classification:** **TEST_BUG** (S1 checklist result table: "Scan command
  matches its own regex example → rewrite the check to avoid self-match").
- **Fix (check only, no product change):** tightened the `private_mount` pattern
  from `/data/home[A-Za-z0-9._/-]*` to `/data/home[_/][A-Za-z0-9][A-Za-z0-9._/-]*`,
  requiring a real name component after the root. This mirrors why `/home/[a-z]`
  never matched (`[` is not a path char), so documented patterns (`/data/home'`,
  `/data/home_[^ ]+`) no longer match while a real `/data/home_<user>/…` leak still
  does. No files were excluded (no blind spots). Re-run: 0 findings.

## FA-2 — Contract WebUI check omits the required `pnpm build`

- **Symptom:** the literal contract deterministic check #3
  (`pnpm install --frozen-lockfile && pnpm lint && pnpm typecheck && pnpm test`)
  fails at `pnpm typecheck` (exit 2) on a fresh tree.
- **Evidence:** `tsc --noEmit` reports 14 `error TS2307: Cannot find module
  './X.module.css'` — Next.js generates the CSS-module (`*.module.css`) type
  declarations during `next build`; without a prior build they do not exist.
  Confirmed: `rm -rf .next && pnpm typecheck` → exit 2; `pnpm build && pnpm
  typecheck` → exit 0. The S4 handoff already anticipated "vitest with next build
  first."
- **Classification:** **SPEC_GAP** (the contract check does not define the build
  prerequisite required for `typecheck` to run).
- **Fix (contract, owner-review):** amended `session_5_contract.yaml`
  `deterministic_checks` #3 to insert `pnpm build` before `pnpm lint`/`typecheck`.
  `.github/workflows/ci.yml` and `docs/session_5/local_checks.md` already run
  `build` first. No product/source change. **Owner: please review/keep this
  amendment** (same posture as S4 FA-4).

## FA-3 — `$PRIVATE_REF_PATTERN` is unset

- **Symptom:** the contract check `rg -n "$PRIVATE_REF_PATTERN" …` expands to an
  empty pattern because the variable is unset in the environment.
- **Evidence:** identical to the `MIG-S1` baseline (see
  `docs/session_1/scrub_checklist.md` §"Baseline Result From Session 1").
- **Classification:** **ENVIRONMENT** (not a product defect).
- **Resolution (no product fix):** the committed `tests/test_private_ref_scan.py`
  encodes the S1 fallback signals (high-confidence secrets + private absolute paths
  + weight/media files) and runs in CI and via CLI; the raw S1 fallback `rg`
  pattern over the code surface (`.github api webui tests schemas`) also returns no
  match. The broad lexical name-assignment scan stays a human-reviewed S8 gate.

## Summary

| ID | Category | Product code changed? | Resolution |
|---|---|---|---|
| FA-1 | TEST_BUG | No | Tightened scanner pattern; 0 findings |
| FA-2 | SPEC_GAP | No | Amended contract check to add `pnpm build` (owner-review) |
| FA-3 | ENVIRONMENT | No | Committed scanner + fallback `rg`; broad scan → S8 |

No `BUG` or `AMBIGUITY` arose. No runtime source, schema content, or public API
behavior (INV-9) was changed to make a check pass.
