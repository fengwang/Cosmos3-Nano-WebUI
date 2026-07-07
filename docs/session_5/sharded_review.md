# Session 5 Sharded Review - CPU-Only CI and Test Stabilization

Session: MIG-S5 · Gate: `GATE-MIG-S5-CI`

## Method

Five independent, read-only reviewers over `git diff 009d66b..HEAD` against
`docs/session_5_contract.yaml` (axes per `docs/agent_workflow/prompts/sharded_review.md`):
correctness, security/safety, tests, architecture/maintainability, performance.
Findings deduplicated below. **No Critical or High findings.** Two Medium findings
(each with concrete evidence and/or 2-reviewer agreement) plus the cheap
high-value Low/Nit items were fixed; the remainder are accepted with rationale.

## Findings and dispositions

| # | Axis(es) | Severity | Finding | Disposition |
|---|---|---|---|---|
| F1 | tests | Medium | `test_clean_tree_has_no_findings` could pass hollow: a bug making the walk visit nothing (wrong root, all-excluded, swallowed `OSError`) yields `[]` → green on zero coverage. | **Fixed** |
| F2 | tests, correctness | Medium | GPU-skip guard (`gpu_test_isolation`) had zero committed coverage — no `@pytest.mark.gpu` test exists; the skip branch was never exercised. | **Fixed** |
| F3 | security | Low | Scanner missed the GitHub PAT class (`ghp_` / `github_pat_` prefixes) — the token most likely pasted into a `.github/` workflow (R-14). | **Fixed** |
| F4 | tests | Low | Positive-detection tests asserted list-truthiness, not which rule fired (weak assertion). | **Fixed** |
| F5 | performance | Info | `(*SECRET_PATTERNS, *PRIVATE_PATH_PATTERNS)` tuple rebuilt once per line. | **Fixed** (hoisted `ALL_PATTERNS`) |
| F6 | correctness | Nit | `/mnt/` private paths uncovered vs the S1 fallback pattern. | **Fixed** (added `mnt_path`, verified clean tree) |
| F7 | performance | Low | `scan_tree` reads the working tree; the gitignored `webui/tsconfig.tsbuildinfo` (327 KB single line) cost ~6 ms locally. | **Fixed** (added `.tsbuildinfo` to `EXCLUDE_SUFFIXES`) |
| F8 | architecture | Low | `tasks.md` §1.3 and `brainstorming.md` Q2 listed 4 `test-cpu` deps; the shipped set is 5 (adds `safetensors`). | **Fixed** (doc updated) |
| F9 | security | Info | Third-party actions pinned to mutable major tags (`@v4`/`@v5`), not SHAs. | **Accepted** |
| F10 | security | Low | `uv.lock` / `pnpm-lock.yaml` excluded from the content scan (credential-in-URL blind spot). | **Accepted / deferred to S8** |
| F11 | correctness | Nit | Leading `\b` on token patterns misses a secret glued to a preceding word char. | **Accepted** |
| F12 | architecture | Low | Doc pack references outputs not yet in the tree (evidence/risk updates, `eval_corpus/mig_s5_*`, this review, adversarial verification). | **Resolved by close-out** (tasks 8–9) |
| F13 | architecture | Nit | `conftest.py` hook signature `(items)` differs from `plan.md`'s `(config, items)`. | **No change** (impl correct; pytest binds by name; documented) |
| F14 | security | Info | `pull_request` from forks. | **No change** (verified safe: no `pull_request_target`, no secrets, `contents: read`) |

## Fixes applied

- **F1/F2 (Medium):** refactored `scan_tree`/`_iter_files` to thread `repo_root` (so
  the scan is exercisable against a synthetic tree), then added:
  `test_scan_tree_walks_a_nonempty_file_set` (asserts the walk visits `api/app/main.py`),
  `test_scan_tree_detects_a_planted_secret_end_to_end` and
  `test_scan_tree_detects_planted_weight_file` (temp-tree, real `os.walk`+read path);
  and new `tests/test_gpu_marker_policy.py` (truthy parsing + the collection hook
  skips a `gpu` fake item off-opt-in with a reason naming `COSMOS3_ENABLE_GPU_TESTS`,
  leaves non-`gpu` items untouched, and runs `gpu` items when opted in).
- **F3:** added `github_pat` (`ghp_`+36) and `github_fine_grained_pat` patterns with
  concatenation-built fixtures.
- **F4:** positive-detection tests now assert the specific `rule` name.
- **F5/F6/F7:** `ALL_PATTERNS` hoisted; `mnt_path` added; `.tsbuildinfo` excluded.
- **F8:** `tasks.md` §1.3 and `brainstorming.md` Q2 now list `safetensors`.

Post-fix verification: `ruff check api tests` → 0; full CPU suite **485 passed, 0
skipped**; scanner CLI clean-tree → **0 findings** (new `/mnt/` + GitHub-token
patterns introduce no false positive).

## Accepted / deferred (rationale)

- **F9 (unpinned major tags):** blast radius is bounded — the workflow has no
  secrets and only `contents: read`, so a poisoned action runs on an ephemeral
  runner with no exfiltratable credentials and no repo write. SHA-pinning is a
  future hardening, noted in the handoff.
- **F10 (lockfile content excluded):** current lockfiles resolve only to public
  indexes (pypi / pythonhosted / download.pytorch.org). Credential-in-URL and the
  broad S1 lexical name-assignment scan stay a human-reviewed **S8** release step,
  per `docs/session_1/scrub_checklist.md`'s classification guidance.
- **F11 (`\b` on tokens):** real leaked tokens are preceded by `=`, quote, colon,
  space, or slash (all satisfy `\b`); dropping the boundary to catch a token glued
  onto an identifier would raise false-positive risk for marginal gain.
- **F12:** the pending outputs are produced at session close (evidence map, risk
  register, eval corpus, this review, adversarial verification, handoff).
- **F13:** pytest binds hook arguments by name, so `(items)` is valid and cleaner;
  the file documents this. `plan.md` is a historical planning artifact.
