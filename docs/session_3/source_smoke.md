# Session 3 Source Smoke Evidence

Date: 2026-07-06
Session: MIG-S3

Environment: torch-free Python 3.12.12 venv built with `uv sync --frozen` (server
core + dev group; the `oracle` extra is NOT installed, so `torch`/`numpy`/
`diffusers`/`transformers` are absent — the CPU/CI-like loop). uv.lock resolved
offline from cache, which also confirms `pyproject.toml`/`uv.lock` install from
public inputs.

## Python (required, deterministic)

| Check | Command | Result |
|---|---|---|
| Byte-compile | `python -m compileall -q api` | **exit 0** |
| Torch-free import graph | `PYTHONPATH=api python -c "import app.main"` | **OK** (FastAPI app builds; logs an expected "transformers unavailable → char heuristic" torch-free fallback) |
| CPU test suite | `pytest -m "not gpu"` | **exit 0**; ~470 tests collected, **467 passed, 3 skipped, 0 failed/error**; the 3 skips are numpy-dependent (numpy absent); gpu-marked deselected for the S8 gate |
| OpenAPI schema sync | `pytest tests/test_openapi.py::test_committed_openapi_matches_live_app` | **pass** — committed `schemas/openapi.json` equals the live app's `openapi_dict()` (no drift) |
| Tools compile | `python -m compileall -q tools` | **exit 0** |

Note: the pytest terminal summary line is suppressed by the project's `-q` addopts
in this pytest build, so the pass count is evidenced by exit code 0, the absence of
any FAILED/ERROR node, and the 100% progress bar.

## WebUI (best-effort, D8) — toolchain available (node 26.4.0 / pnpm 11.3.0)

| Check | Command | Result |
|---|---|---|
| Install | `pnpm install --frozen-lockfile --prefer-offline` | **OK** (offline from store, ~0.9 s) |
| Typecheck | `pnpm typecheck` (`tsc --noEmit`) | **OK** after the Next-generated `next-env.d.ts` is present (see failure_arbiter.md: ENVIRONMENT) |
| Unit tests | `pnpm test` (`vitest run`) | **39 files, 208 tests, all passed** |
| Lint | `pnpm lint` (`eslint .`) | **clean** |

Generated artifacts (`node_modules/`, `.next/`, `next-env.d.ts`) were removed after
the checks and are not committed.

## Pre-existing findings (not introduced by import; not S3 scope)

- Pyright reports unresolved `modelopt`/`diffusers`/`vllm` imports — these are the
  deliberately-deferred heavy imports, unresolved in the torch-free analysis env
  (by design). ENVIRONMENT.
- Pyright reports `Orchestrator | None` typing nits in `api/app/main.py`
  (lines 179–201) and unresolved `engines.*` imports (Pyright is not configured
  with `pythonpath=["api"]`). Pre-existing / tooling-config; pytest resolves them.
- `tests/checkpoint_prep/test_copy_shared_integration.py:170` has a trailing blank
  line at EOF (imported verbatim). Nit; ruff (configured in `pyproject`) will
  normalize it in S5 CI.

All deterministic contract checks pass or are classified. See
`docs/session_3/failure_arbiter.md`.
