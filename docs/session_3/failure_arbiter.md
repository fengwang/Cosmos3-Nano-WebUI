# Session 3 Failure Arbiter

Date: 2026-07-06
Session: MIG-S3

Every failing check or collection error was classified before any fix, per the
Failure Arbiter protocol (BUG / SPEC_GAP / AMBIGUITY / ENVIRONMENT / TEST_BUG).

## FA-1: `tests/api/test_s7_evidence_lib.py` collection error

- **Symptom:** `pytest -m "not gpu"` aborted collection with
  `FileNotFoundError: .../docs/session_7/outputs/evidence_lib.py`.
- **Cause:** the test dynamically loads (`spec_from_file_location` + `exec_module`)
  an evidence-harness module that lives under the private repo's
  `docs/session_7/outputs/` — excluded private development docs.
- **Classification:** AMBIGUITY (curation boundary). The test targets a private
  evidence-harness lib, not public product source, and cannot run from public
  inputs.
- **Resolution:** exclude the test (recorded in `import_manifest.md`). No product
  code changed. Its evidence role belongs to the S7/S8 harness sessions.

## FA-2: `test_action_metrics.py` + `test_reasoning_metrics.py` depend on excluded code

- **Symptom:** straggler scan flagged `from equivalence.metrics.{action,reasoning}
  import …`; `equivalence.metrics` lives under the excluded `tests/equivalence/`.
- **Cause:** these top-level tests are equivalence-suite metric unit tests that
  import the `equivalence` package.
- **Classification:** AMBIGUITY. Re-including `tests/equivalence/metrics/` would
  blur the D5 exclusion boundary and pull numpy/perceptual deps; the two tests
  belong with the deferred equivalence suite.
- **Resolution:** exclude both tests (consistent with D5). Coverage deferred to the
  S8 manual-gate/equivalence session.

## FA-3: WebUI `tsc --noEmit` reports `TS2307: Cannot find module './*.module.css'`

- **Symptom:** standalone `pnpm typecheck` failed on a subset of CSS-module imports.
- **Cause:** the Next.js-generated `next-env.d.ts` (which supplies `*.module.css`
  ambient typing) is gitignored in the source and therefore not imported. All 25
  `.module.css` files ARE present; nothing is missing.
- **Classification:** ENVIRONMENT (missing generated file). Confirmed: generating
  the canonical `next-env.d.ts` makes `tsc --noEmit` pass with zero errors.
- **Resolution:** no source change. The WebUI typecheck must run after a Next build
  step (which regenerates `next-env.d.ts`); this CI wiring is MIG-S5 scope. Recorded
  in the handoff.

## FA-4: Pyright unresolved imports + `main.py` typing nits (pre-existing)

- **Symptom:** editor diagnostics: unresolved `modelopt`/`diffusers`/`vllm`;
  `Orchestrator | None` assignment nits in `api/app/main.py`; unresolved
  `engines.*` in tests.
- **Cause:** deferred heavy imports are unresolved in a torch-free analysis env (by
  design); Pyright is not configured with `pythonpath=["api"]`. None introduced by
  this session's edits (edits were checkpoint-name string/comment changes only).
- **Classification:** ENVIRONMENT / pre-existing. Not a runtime defect — `compileall`,
  `import app.main`, and pytest all pass.
- **Resolution:** no change (INV-9; out of S3 scope). Typecheck-gate policy is S5.

## FA-5: Trailing blank line at `test_copy_shared_integration.py:170` (pre-existing Nit)

- **Symptom:** `git diff --check` flagged a blank line at EOF.
- **Cause:** imported verbatim from the private source.
- **Classification:** TEST_BUG-adjacent Nit (style).
- **Resolution:** left verbatim; ruff (configured in `pyproject`) normalizes it in
  S5 CI. REVIEW.md: do not report style already enforced by the linter.

## FA-6: Private values leaked in the session's own public docs (caught by sharded review)

- **Symptom:** the security-axis reviewer found the initial `docs/session_3/**` named
  private values (the private source checkout path, the private intranet host, and a
  sibling private repo name), matching the MIG-S2 eval seed
  (`docs/eval_corpus/mig_s2_private_source_scrub.md`).
- **Cause:** the refining-pack docs quoted the owner-provided answers verbatim.
- **Classification:** **BUG against INV-1** (and PRD FR-2 / NFR-1). The imported source
  tree was already clean; the leak was only in the committed docs.
- **Resolution:** redacted all such literals to policy/descriptor language and generic
  detectors across the 8 affected docs; the MIG-S2 regression over `docs/session_3/**`
  is now clean. See `scrub_report.md` "Sharded-Review Correction".

## Conclusion

One BUG (FA-6, a docs INV-1 leak) was caught by sharded review and fixed. No product-code
fix was required to make the deterministic checks pass; the remaining items are curation
exclusions, ENVIRONMENT (generated file / analysis env), and pre-existing Nits deferred
to MIG-S5.
