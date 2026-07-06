# Session 5 Brainstorming - CPU-Only CI and Test Stabilization

Date: 2026-07-07
Session: MIG-S5
Status: Validated design (owner-approved)
Risk: medium · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S5-CI`

## Project Context

The public beta needs a reliable quality gate that runs without model weights,
CUDA, private network access, or self-hosted runners (PRD §3.10, INV-5). Sessions
1–4 delivered the docs pack, the pinned vLLM-Omni fork (S2), the curated API/WebUI
import (S3), and the Hugging Face checkpoint verification + `docs/model_setup.md`
(S4). No `.github/` workflows exist yet; Session 5 builds CPU CI from scratch.

Baseline measured on the build host (repo-relative evidence only):

- Toolchain present: `uv 0.11.25`, `pnpm 11.3.0`, `node v26.4.0`, host `python3`
  `3.14`. The project requires Python `>=3.12,<3.13` (`pyproject.toml`), so CI and
  local runs MUST provision 3.12 through `uv`, never the host interpreter.
- `uv sync --frozen` installs the torch-free core + `dev` group cleanly (no
  `oracle`/torch). Confirmed reproducible.
- `ruff check api` → clean (exit 0). `ruff check tests` → **FAIL (exit 1, 2
  errors)**: `F541` f-string without placeholders (`tests/api/test_gen_ipc.py:232`)
  and `E402` module import not at top (`tests/api/test_oracle_adapter_audio.py:46`,
  an intentional `sys.modules` stub-before-import).
- `pytest -m "not gpu"` → **PASS (exit 0)**, 3 skips (all `numpy` `importorskip`
  gates: `tests/checkpoint_prep/test_writer_format.py:15`,
  `tests/api/test_artifact_encoders.py:{46,55}`). The suite already includes
  `tests/test_openapi.py` (app↔`schemas/openapi.json` drift), which is torch-free.
- The `gpu` pytest marker is registered (`pyproject.toml`) but applied to **zero**
  tests — S3 imported only CPU-safe tests. `-m "not gpu"` currently deselects
  nothing; the marker is forward-looking policy.
- `webui/` uses `pnpm@11.3.0`, Next 15 / React 19. `webui/tsconfig.json` includes
  `.next/types/**/*.ts` and the Next plugin, so `tsc --noEmit` likely needs a prior
  `next build`. `api/app/openapi_export.py` exists; the app→`openapi.json` and
  `openapi.json`→`schema.d.ts` sync layers are both torch-free.
- No `deploy/` directory yet (Docker is S6) → render-only Docker/Compose checks are
  N/A this session (in-scope item is conditional: "if deploy files exist").

## Clarifying Questions and Owner Decisions

| # | Question | Decision |
|---|---|---|
| Q1 | Run `next build` in CI (needed by typecheck's `.next/types`; validates bundle)? | **Yes — build first** (`gen:api → build → lint → typecheck → test`); verify empirically. |
| Q2 | Add a torch-free CPU test extra so the 3 numpy-skipped encoder tests run? | **Yes** — add `numpy + pillow + imageio + imageio-ffmpeg` (mitigates hollow-pass, `EV-MIG-IMPORT-COMPLETE`). |
| Q3 | How to implement the private-reference/secret scan (contract's 5th check)? | **Committed scrub script**, scoped to avoid self-match (`EV-MIG-SCRUB-COMMAND-SANITY`). |
| Q4 | How much GPU forward-safety hardening? | **`tests/conftest.py` guard + CI `-m "not gpu"`** (defense-in-depth). |

Defaults accepted by the owner: Node **22 LTS** in CI (host Node 26 is
bleeding-edge; CI must be reproducible); a single `.github/workflows/ci.yml` with
parallel jobs; triggers `push` + `pull_request`, `permissions: contents: read`, no
secrets, concurrency cancel-in-progress; local commits on `session-5`, **no push /
no PR** (mirrors S2–S4).

D10 contract-authority note approved: the Session End Protocol requires
`docs/handoff.md` + `docs/eval_corpus/**` (+ possibly `docs/eval_seed_cases.md`),
which are outside S5 `allowed_files`. The owner approved a small contract amendment
to `session_5_contract.yaml` adding those paths (precedent: S4 FA-4).

## Approaches Considered (workflow topology)

- **A — one `ci.yml`, two parallel jobs (`python`, `webui`)** *(chosen)*. Single
  status check, minimal duplicated setup, easy to reason about, parallel wall-clock.
- **B — split `python.yml` + `webui.yml`.** Independent badges but duplicated
  checkout/setup and two status contexts to wire into branch protection later.
- **C — one sequential job.** Rejected: serial wall-clock and poor isolation
  between Python and Node toolchains.

## Validated Design

- **D1 · Topology.** `.github/workflows/ci.yml`; `on: [push, pull_request]`;
  `permissions: contents: read`; `concurrency` with `cancel-in-progress`; no
  secrets; `ubuntu-latest`; two parallel jobs.
- **D2 · Python job** (`EV-MIG-PY-UNIT`, app-side schema sync, scrub):
  `astral-sh/setup-uv` (pinned + cache) → `uv python install 3.12` →
  `uv sync --frozen --group test-cpu` (core+dev+CPU test deps, no `oracle`) →
  `uv run ruff check api tests` → `uv run pytest -m "not gpu"` (includes
  `test_openapi.py` and the new `test_private_ref_scan.py`).
- **D3 · WebUI job** (`EV-MIG-WEBUI-UNIT`, types-side schema sync):
  `pnpm/action-setup` (11.3.0) + `actions/setup-node` (Node 22, pnpm cache) →
  `pnpm install --frozen-lockfile` → `pnpm gen:api && git diff --exit-code
  lib/api/schema.d.ts` → `pnpm build` → `pnpm lint` → `pnpm typecheck` →
  `pnpm test`. `NEXT_TELEMETRY_DISABLED=1`. Build/typecheck dependency confirmed
  empirically before finalizing.
- **D4 · Schema-sync gate.** Two torch-free layers, both already present:
  app→`openapi.json` (`tests/test_openapi.py`); `openapi.json`→`schema.d.ts`
  (`pnpm gen:api` + `git diff --exit-code`).
- **D5 · Scrub gate.** `tests/test_private_ref_scan.py` (blast-radius-legal home;
  `tools/**` is not allowed): a pure scan function (Calculation) + pytest wrapper +
  `__main__` CLI. High-confidence secret patterns (private-key headers, `hf_…` /
  `sk-…` tokens), weight/media extensions committed as files, and known-private
  tokens; allowed `/path/to/…` placeholders; self-exclusions (the checklist +
  scanner file). Verified zero findings on the clean tree before use.
- **D6 · GPU forward-safety.** `tests/conftest.py` collection hook auto-skips
  `@pytest.mark.gpu` tests unless `COSMOS3_ENABLE_GPU_TESTS` is set; CI also passes
  `-m "not gpu"`. Documented convention: gpu modules guard heavy imports via
  `importorskip`. Manual command `COSMOS3_ENABLE_GPU_TESTS=1 pytest -m gpu` → S8.
- **D7 · Baseline fixes.** `F541` → drop stray `f` prefix; `E402` → inline
  `# noqa: E402` with a comment; `pyproject.toml` → new `[dependency-groups]
  test-cpu`, regenerating `uv.lock`.
- **D8 · Deliverables.** `ci.yml`, `conftest.py`, scrub test,
  `pyproject.toml`/`uv.lock`, the `docs/session_5/**` refining pack + review /
  verify / failure-arbiter docs + a local-check command list, and
  `docs/evidence_map.md` / `docs/risk_register.md` updates (R-05/R-10/R-14).
- **D9 · Risks → mitigations.** `next build` network/flakiness → telemetry off,
  empirical verify, classify `ENVIRONMENT` if flaky. Scrub false positives →
  scoped patterns + allowlist + baseline-clean gate. Hollow-pass → `test-cpu`
  extra runs the encoder tests; `test_openapi` + scrub are real gates. R-05 → CI
  labeled CPU-only, no GPU claims, manual gate documented.
- **D10 · Contract amendment** (approved): add `docs/handoff.md`,
  `docs/eval_corpus/**`, `docs/eval_seed_cases.md` to `session_5_contract.yaml`
  `allowed_files`.

## Out of Scope (confirmed)

No GPU CI; no Docker image publishing; no secrets/registry credentials; no runtime
checkpoint inference; no Docker/Compose render checks (no `deploy/` yet — hand
`EV-MIG-COMPOSE-RENDER` to S6); no `README.md` edits (S7); no push / PR.
