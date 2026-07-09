# Session 5 Adversarial Verification - CPU-Only CI and Test Stabilization

Session: MIG-S5 · Gate: `GATE-MIG-S5-CI`

## Method

A fresh-context verifier (no access to the implementation conversation) saw only
`docs/session_5_contract.yaml`, `docs/project_contract.md`,
`docs/session_5/execution_contract.md`, and `git diff 009d66b..HEAD`, and was tasked
to **falsify** "GATE-MIG-S5-CI passes with CPU-only public CI ready for the beta
branch." It ran every check itself (per
`docs/agent_workflow/prompts/adversarial_verifier.md`) and reverted all probe edits
(working tree confirmed clean, HEAD unchanged afterward).

## Verdict: PASS (two disclosed caveats)

### Independently reproduced (command evidence)

- `uv run ruff check api tests` → exit 0.
- `uv run pytest -m "not gpu"` → **485 passed, 0 skipped, 0 deselected**; `torch`
  absent in the `test-cpu` venv. Confirmed **not hollow**: the artifact-encoder /
  writer tests execute because `test-cpu` supplies the `importorskip` deps.
- WebUI: `pnpm gen:api` + `git diff --exit-code lib/api/schema.d.ts` → no drift;
  `pnpm build && pnpm lint && pnpm typecheck && pnpm test` → all exit 0; vitest
  208 passed / 39 files.
- `uv run python tests/test_private_ref_scan.py` → clean, 0 findings.
- `.github/workflows/ci.yml`: `permissions: contents: read`, `ubuntu-latest`, no
  `secrets.`, no self-hosted, no CUDA, never `--extra oracle` (INV-5).

### Adversarial cases — all defeated

- **Hollow pass:** refuted — 485 real tests run, nothing mass-skipped.
- **Needs a secret:** refuted — none referenced.
- **Schema drift escapes CI:** refuted on **both** layers — the verifier injected a
  property into `schemas/openapi.json` (→ `tests/test_openapi.py` failed) and a
  type-affecting change (→ `pnpm gen:api` + `git diff --exit-code` failed), then
  reverted both.
- **Scanner false neg/pos:** refuted — planted `sk-…` and a `/home/<user>` path in
  `docs/` were detected; the real tree scans clean.
- **GPU import breaks CPU collection:** the verifier confirmed the *latent* risk
  (an unguarded top-level `import torch` in a hypothetical new `gpu` test would fail
  CPU collection even with `-m "not gpu"`), but the current tree has **zero** `gpu`
  tests, the 485-suite collects cleanly, and `tests/conftest.py` documents the
  required import-guard convention. Documented convention, not a present defect.

### Invariants: INV-5, INV-9 (diff touches no `api/`, `schemas/`, or webui product
code — only `tests/**`, workflow, docs, `pyproject.toml`, `uv.lock`), and INV-10
(`test-cpu` torch-free, test-only) all upheld.

## Caveats raised (and disposition)

1. **Done-condition item 9 (handoff / evidence / eval-seed updates) not yet in the
   diff at verification time.** Correct — verification ran before the close-out
   step; `docs/handoff.md`, `docs/evidence_map.md`, `docs/risk_register.md`,
   `docs/eval_seed_cases.md`, and `docs/eval_corpus/mig_s5_*` are produced in the
   session close-out (task 9) that follows this verification. Re-check the final
   commit for item 9.
2. **The session edited its own `session_5_contract.yaml`** (D10 `allowed_files`
   amendment + FA-2 `deterministic_checks` amendment), which is not covered by its
   own `allowed_files`. Both edits are disclosed in-file with owner-approval
   comments and in `failure_arbiter.md` FA-2 (posture mirrors S4 FA-4). Flagged for
   owner review; not a silent violation.

Both caveats are governance/close-out items, not defects in the CI itself; neither
falsifies the CPU-CI-readiness claim.
