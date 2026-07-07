# Session Handoff

## State Snapshot

- Session: MIG-S5, CPU-Only CI and Test Stabilization
- Branch: WebUI repo `session-5` (local commits only; not pushed)
- Last commit at close: `docs(s5): review, adversarial verification, evidence/risk, handoff`
- Workflow added: `.github/workflows/ci.yml` — one workflow, two parallel
  `ubuntu-latest` jobs: **`python`** (lint + CPU tests + schema/scrub gates) and
  **`webui`** (schema sync + build + lint + typecheck + unit tests).
- Changed files (all within the amended `allowed_files`):
  - New: `.github/workflows/ci.yml`, `tests/conftest.py`,
    `tests/test_private_ref_scan.py`, `tests/test_gpu_marker_policy.py`
  - Edited: `tests/api/test_gen_ipc.py` (F541), `tests/api/test_oracle_adapter_audio.py`
    (E402 noqa), `pyproject.toml` (`test-cpu` group), `uv.lock` (regenerated)
  - Docs: `docs/session_5/**` (refining pack + `local_checks.md` +
    `failure_arbiter.md` + `sharded_review.md` + `adversarial_verification.md`),
    `docs/evidence_map.md`, `docs/risk_register.md` (R-05/R-10/R-14),
    `docs/eval_seed_cases.md`, `docs/eval_corpus/mig_s5_*.md`, `docs/handoff.md`
  - Contract: `docs/session_5_contract.yaml` (D10 `allowed_files` + FA-2
    `deterministic_checks` amendments — **owner review requested**)
- Checks run (host: `uv 0.11.25` provisioning Python 3.12; `pnpm 11.3.0`, Node
  present; live network for installs):
  - `uv run ruff check api tests` = **0**
  - `uv sync --frozen --group test-cpu` (torch-free) then `uv run pytest -m "not gpu"`
    = **485 passed / 0 skipped** (was 467 passed / 3 numpy-skipped)
  - `pytest -q` (no marker filter) = 0 (conftest guard skips any `gpu` test)
  - WebUI: `pnpm install --frozen-lockfile`; `pnpm gen:api` + `git diff --exit-code
    lib/api/schema.d.ts` (in sync); `pnpm build` → `pnpm lint` → `pnpm typecheck` →
    `pnpm test` (**vitest 208 passed / 39 files**) — all 0
  - `uv run python tests/test_private_ref_scan.py` = **clean (0 findings)**
  - Schema drift proven to fail CI on **both** layers (adversarial verifier injected
    drift into `openapi.json` → `test_openapi.py` failed; type-affecting change →
    `gen:api` diff failed; both reverted)
  - Sharded review (5 axes): **no Critical/High**; Medium/Low fixed
  - Fresh-context adversarial verifier: **PASS** (reproduced all checks; tree left clean)
- Checks not run (correctly out of scope):
  - The GitHub-hosted Actions run itself (no push; first real run on `MIG-S6`/`MIG-S8`)
  - GPU inference / RTX 5090 (manual gate, `MIG-S8`; R-05 still open)
  - Docker/Compose render checks (no `deploy/` yet → `MIG-S6`, `EV-MIG-COMPOSE-RENDER`)
  - Playwright e2e (not part of CPU CI this session)
- Current status: **`GATE-MIG-S5-CI` is satisfied.** CPU-only public CI exists and is
  secret/CUDA/weight/self-hosted-free (INV-5), CPU lint + tests pass non-hollow, both
  schema-sync layers fail on drift, GPU tests are isolated, and the private-reference
  scan is clean — all reproduced by an independent adversarial verifier.

## Narrative Context

Session 5 built the CPU-only quality gate from scratch (`.github/` did not exist).
It fixed the one broken deterministic check (`ruff check tests` → 2 errors), added a
torch-free `test-cpu` dependency group so previously-skipped artifact-encoder /
writer tests actually execute (defeating the "hollow pass" adversarial case), added
a `tests/conftest.py` guard + `-m "not gpu"` so GPU tests can never run or break
collection in CPU CI, and added a committed `tests/test_private_ref_scan.py`
(pure-scan + pytest gate + CLI) for secret/private-path/weight detection. The WebUI
job must `next build` before `typecheck` (Next generates CSS-module type
declarations at build time) — a contract SPEC_GAP that was classified and amended.

## Decision Log

| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| CI topology | One `ci.yml`, two parallel jobs | Split files / one sequential job | Single status, parallel, minimal duplication | `design.md` D-1 |
| Python toolchain | `uv`-provisioned 3.12, `--frozen --group test-cpu` | System Python + pip | Host is 3.14; lockfile determinism (R-10) | `design.md` D-2 |
| Anti-hollow-pass | Torch-free `test-cpu` group (+`safetensors`) | Accept the skips | 485/0 skipped; encoder+writer tests run | `design.md` D-3; FA-2 |
| WebUI order | `build` before `typecheck` | Contract's literal order (no build) | typecheck needs Next CSS-module types (verified) | `failure_arbiter.md` FA-2 |
| Schema sync | Two existing torch-free layers | New export tooling | `test_openapi.py` + `gen:api` diff both exist | `design.md` D-5 |
| Scrub home | `tests/test_private_ref_scan.py` (pure fn + CLI) | `tools/**` (out of blast radius); inline YAML `rg`; gitleaks | Blast-radius-legal, testable, no 3rd-party action | `design.md` D-6 |
| GPU isolation | conftest guard + `-m "not gpu"` | CI flag only | Two independent mechanisms | `design.md` D-7 |
| Node in CI | 22 LTS | Match host (26) | Reproducible; lockfile drives resolution | brainstorming defaults |
| Contract edits | Amend `session_5_contract.yaml` (D10 + FA-2), flag for owner | Leave protocol/contract gaps | Session End Protocol + FA-2 need it; S4 FA-4 precedent | `failure_arbiter.md` FA-2 |

## Next Priority Queue

1. `MIG-S6` (Docker/Compose): once `deploy/` exists, add a render-only
   `EV-MIG-COMPOSE-RENDER` job to `ci.yml` (Compose config render, no private paths,
   no baked weights). **Must resolve S4 drift D1** (validate the default `vllm_omni`
   container loader against the public FP8 **and** NVFP4 checkpoints). Consume
   `docs/model_setup.md` for env/mount/revisions.
2. `MIG-S7` (README + hygiene): re-run the scrub (`tests/test_private_ref_scan.py`)
   over README/hygiene content; keep model license (`openmdw-1.0`) separate from repo
   MIT; use the correct base id `nvidia/Cosmos3-Nano`. Consider a `.gitignore`
   hygiene pass (see gotcha below) — needs a contract amendment (out of S5 radius).
3. `MIG-S8` (release gate): run manual GPU gates for the full surface; review R-05
   (CPU-green-while-GPU-broken); run the broad S1 lexical scan + lockfile-URL
   credential scan as the human-reviewed gate; review whether to SHA-pin CI actions.

## Warnings And Gotchas

- **Environment:** host `python3` is 3.14 but the project pins `>=3.12,<3.13` — always
  use `uv` (never host Python). WebUI: `pnpm typecheck` FAILS unless `pnpm build` ran
  first (CSS-module types). CI pins Node 22; local dev on newer Node is fine.
- **CI first run:** `ci.yml` has not executed on GitHub Actions yet (no push). The
  first real run happens on `MIG-S6`/`MIG-S8`; action major-tag pins (`@v4`/`@v5`)
  should be confirmed to resolve then.
- **Scanner scope:** `tests/test_private_ref_scan.py` walks the working tree (not
  `git ls-files`) and excludes `.venv`/`node_modules`/`.next`/`__pycache__`/lockfiles/
  `.tsbuildinfo`. It catches high-confidence secret *values* + private absolute paths +
  weight files; the **broad lexical name-assignment scan and lockfile-URL credential
  scan remain a human-reviewed `MIG-S8` gate** (`$PRIVATE_REF_PATTERN` is unset —
  ENVIRONMENT, per S1).
- **Repo hygiene gap (out of S5 blast radius):** the root `.gitignore` does not cover
  `.venv/`, `__pycache__/`, `node_modules/`; local check runs create these. Only
  explicit `git add <path>` was used this session. A `.gitignore` pass is a candidate
  for `MIG-S7` (needs a contract amendment).
- **Deferred risks:** R-05 (CPU-CI-green-while-GPU-broken) still **open** → S8;
  D1 (vllm_omni checkpoint load) → S6; Docker build/render → S6.
- **Files future sessions must not casually edit:** `schemas/openapi.json` (regenerate
  only, never hand-edit — INV-9 public API shape), public API route/request shapes,
  `pyproject.toml`/`uv.lock` pins. Do not name private paths/hosts/dev-variants in any
  scanned doc (the CI scrub will fail).
- **Contract note:** `session_5_contract.yaml` was amended twice (D10 `allowed_files`;
  FA-2 `deterministic_checks` adding `pnpm build`) — change-controlled file touched;
  **owner may review/keep** (mirrors S4 FA-4).

## Eval Seeds

- New regression candidates (added to `docs/eval_corpus/`):
  - `mig_s5_scrub_scanner_self_match.md` — a scrub scanner must not flag its own /
    prior sessions' pattern documentation (TEST_BUG; tighten pattern + exclude
    scanner/checklist + concat fixtures).
  - `mig_s5_next_typecheck_needs_build.md` — Next.js `typecheck` requires a prior
    `build` (SPEC_GAP; order build before typecheck in contract + CI).
  - `mig_s5_hollow_gate_and_marker_coverage.md` — an "absence" gate and an unmarked
    marker guard both need explicit coverage assertions.
- Instruction-update candidate (REVIEW.md / project contract template): (a) for a
  Next.js app, `build` precedes `tsc` typecheck; (b) a committed scrub scanner MUST be
  sanity-tested against its own pattern docs; (c) a gate whose green state is "no
  findings" MUST assert it actually ran (walked files / catches a planted positive).
