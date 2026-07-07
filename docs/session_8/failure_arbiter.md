# Failure Arbiter - MIG-S8

Classifications raised during the S8 release gate (sharded review). No product-code fix is
applied without owner approval; out-of-radius fixes need a blast-radius amendment.

## FA-1 — S8 check #15 abspath sub-scan was silently broken (TEST_BUG)

- **Failing command:** the `deterministic_checks.md` #15 "absolute non-placeholder path
  scan": `... rg -nH "(/home/[a-z]|/Users/|/root/|/workspace/github\.repo/(?!Cosmos3-Nano-WebUI))" ... 2>/dev/null`.
- **Symptom:** reported "clean", but a counterexample exists (`/workspace/github.repo/vllm-omni`
  in `evidence_map.md:21`), surfaced by the security + tests reviewers.
- **Root cause:** `rg` uses the Rust regex engine, which does **not** support look-around;
  the `(?!Cosmos3-Nano-WebUI)` negative lookahead makes the pattern invalid, `rg` exits 2,
  and `2>/dev/null` swallows the error → the loop produced no output → false "clean".
- **Category:** **TEST_BUG** (the check contradicted reality by construction; not a product
  defect). Not BUG (no product code involved), not ENVIRONMENT (deterministic mis-authoring),
  not AMBIGUITY (the intent was clear).
- **Allowed next action:** re-run a valid scan (no look-around; post-filter the sanctioned
  `/path/to/` and the repo's own `Cosmos3-Nano-WebUI` self-path), record the exact commands +
  exit codes, and reflect the true result in #15. Fix the in-radius leak it exposed.
- **Forbidden next action:** editing product code; leaving #15 as an unreproducible prose
  "clean". Both addressed.

## FA-2 — `/workspace/…` local paths in OUT-OF-RADIUS historical docs (SPEC_GAP / blast-radius)

- **Finding:** the ground-truth scan (valid regex) shows **24** `/workspace/github.repo/…`
  occurrences in **8 out-of-radius files**: `docs/session_2/**` = 22 (the `vllm-omni` sibling
  checkout — execution_contract 8, failure_arbiter 4, brainstorming 4, proposal 2, plan 2,
  design 1, specs/session_evidence_handoff 1), and `docs/session_3/plan.md` + `docs/session_4/plan.md`
  = 2 (this repo's own checkout `/workspace/github.repo/Cosmos3-Nano-WebUI`). These are tracked
  public files that will ship at publish. (`/home/runner` in `.github`/docs is the public GitHub
  Actions runner home, not private; `/data/home_<user>`-class user paths are **absent** from the tree.)
- **Category:** **SPEC_GAP** — the S8 `blast_radius.allowed_files` does **not** include
  `docs/session_{2,3,4}/**`, yet INV-1 / `project_contract.md` §6 forbid private absolute
  paths / local-only artifact references in public docs. The release gate found a
  public-cleanliness issue in files it is not authorized to edit.
- **Sensitivity:** low — `/workspace/github.repo/...` exposes a local checkout layout, no
  username/host/secret (contrast a real user-home mount of the scanner's `private_mount` class
  — a `/data/home_<user>`-style path — which is **absent** from the tree).
- **Allowed next action:** stop and route to the owner (below). Do **not** edit
  `docs/session_{2,3,4}/**` without an owner-approved blast-radius amendment.
- **Owner decision required (GO condition):**
  - (a) approve a blast-radius amendment to scrub `/workspace/...` → a public phrasing across
    the historical session docs (mechanical; re-verify after), **or**
  - (b) accept `/workspace/...` as non-sensitive / non-blocking for beta (record the
    interpretation; still recommend the scanner gap in FA-3 be closed).
- **Recommendation:** (a) for a clean public release; the fix is trivial and removes the
  class entirely.

## FA-3 — committed scanner misses the `/workspace/` path class and `.webm` (SPEC_GAP / product code)

- **Finding:** `tests/test_private_ref_scan.py` `PRIVATE_PATH_PATTERNS` covers `/home/`,
  `/Users/`, `/mnt/`, `/data/home` but **not** `/workspace/`; `WEIGHT_MEDIA_EXTS` omits
  `.webm`. So the committed gate (#12) is clean by construction for these classes.
- **Category:** **SPEC_GAP** in a product-code test — out of the S8 docs-only blast radius.
- **Impact:** currently no active miss beyond FA-2 (0 `.webm` files exist; the only
  `/workspace/` leaks are FA-1/FA-2, now handled in-radius + routed). But the automated gate
  will not catch a future `/workspace/` or `.webm` leak.
- **Allowed next action:** record a recommendation + eval seed for the owner to add a
  `/workspace/[A-Za-z0-9._/-]+` pattern (post-filtering the repo self-path) and `.webm` to the
  scanner. Do **not** edit the scanner this session (product code).
- **Forbidden next action:** editing `tests/test_private_ref_scan.py` without owner approval.
