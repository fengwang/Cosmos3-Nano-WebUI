# Failure Arbiter - MIG-S8

Classifications raised during the S8 release gate (sharded review). Out-of-radius fixes were
applied only under owner-approved blast-radius amendments (S8-A1, S8-A2). Local checkout paths
are written here in a redacted `/workspace/…` form so this doc does not itself carry a literal
local path (the same discipline the scrub enforces).

## FA-1 — S8 check #15 abspath sub-scan was silently broken (TEST_BUG) — RESOLVED

- **Failing command:** the `deterministic_checks.md` #15 "absolute non-placeholder path scan"
  used an `rg` alternation that included a **negative look-around** on the workspace-path class,
  run with `2>/dev/null`.
- **Symptom:** reported "clean", but a counterexample existed (a `/workspace/…` local path in
  `evidence_map.md:21`), surfaced by the security + tests reviewers.
- **Root cause:** `rg` uses the Rust regex engine, which does **not** support look-around; the
  look-around made the pattern invalid, `rg` exited 2, and `2>/dev/null` swallowed the error →
  the loop produced no output → a false "clean".
- **Category:** **TEST_BUG** (the check contradicted reality by construction; no product code).
  Not BUG, not ENVIRONMENT (deterministic mis-authoring), not AMBIGUITY (intent was clear).
- **Resolution:** #15 rewritten as #15a/#15b/#15c with exact commands + exit codes (no
  look-around; post-filter the sanctioned `/path/to/`, the public `/home/runner`, and the repo
  self-path). The corrected scan found the in-radius leak (fixed) and the out-of-radius set (FA-2).

## FA-2 — `/workspace/…` local paths in OUT-OF-RADIUS historical docs (SPEC_GAP) — RESOLVED via S8-A1

- **Finding:** the corrected scan showed **24** `/workspace/…` occurrences in **8 out-of-radius
  files**: `docs/session_2/**` = 22 (the `vllm-omni` sibling checkout — execution_contract 8,
  failure_arbiter 4, brainstorming 4, proposal 2, plan 2, design 1, specs/session_evidence_handoff
  1), plus `docs/session_3/plan.md` + `docs/session_4/plan.md` = 2 (this repo's own checkout).
  These are tracked public files that ship at publish. (`/home/runner` in `.github`/docs is the
  public GitHub Actions runner home, not private; `/data/home_<user>`-class user paths are
  **absent** from the tree.)
- **Category:** **SPEC_GAP** — the base S8 `blast_radius.allowed_files` did **not** include
  `docs/session_{2,3,4}/**`, yet INV-1 / `project_contract.md` §6 forbid local absolute paths in
  public docs. The release gate found a public-cleanliness issue in files it could not edit.
- **Sensitivity:** low — a `/workspace/…` checkout path exposes a local directory layout, no
  username/host/secret (contrast the scanner's `private_mount` class — a `/data/home_<user>`-style
  path — which is **absent** from the tree).
- **Resolution:** owner approved amendment **S8-A1** (2026-07-07); the sibling-checkout paths were
  rewritten repo-relative (`vllm-omni`) and this repo's own path to the sanctioned
  `/path/to/Cosmos3-Nano-WebUI` placeholder across the 8 files. Re-scan clean. The regex-doc lines
  (`/workspace/[^/]+`) in `session_3/scrub_report.md`/`plan.md` are intentionally left — `[` is
  not a path char, so they are not real paths and do not match the scanner.

## FA-3 — committed scanner missed the `/workspace/` path class and `.webm` (SPEC_GAP) — RESOLVED via S8-A2

- **Finding:** `tests/test_private_ref_scan.py` `PRIVATE_PATH_PATTERNS` covered `/home/`,
  `/Users/`, `/mnt/`, and the `/data/home…` user-mount class but **not** `/workspace/`;
  `WEIGHT_MEDIA_EXTS` omitted `.webm`. So the committed gate (#12) was clean by construction for
  these classes — the blind spot that let FA-1/FA-2 through.
- **Category:** **SPEC_GAP** in a product-code test — out of the base S8 docs-only blast radius.
- **Resolution:** owner approved amendment **S8-A2** (2026-07-07); added a `workspace_path`
  pattern (`/workspace/[A-Za-z0-9._/-]+`) + `.webm` to the scanner, with RED-before-GREEN unit
  tests (`test_private_paths_caught_with_correct_rule` asserts `workspace_path`;
  `test_workspace_ellipsis_form_not_flagged` asserts the `/workspace/…` and `/workspace/[^/]+`
  doc forms are **not** flagged). The scanner now catches this class going forward. Eval seed:
  `docs/eval_corpus/mig_s8_scanner_abspath_blindspot.md`.
