# Contributing to Cosmos3-Nano-WebUI

Thanks for your interest in contributing! This is a **beta / research preview**,
so expect rough edges and moving parts. Contributions of all sizes are welcome:
bug reports, docs fixes, tests, and code.

By participating you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
To report a security vulnerability, follow [SECURITY.md](SECURITY.md) — **not** a
public issue.

## Ways to contribute

- **Report a bug** or **request a feature** using the issue templates (New issue →
  pick a template). Please include enough detail to reproduce.
- **Improve docs** — the README, `docs/model_setup.md`, and deploy notes.
- **Fix a bug or add a test** — see the workflow below.

## Development setup

Prerequisites: Python 3.12 (`>=3.12,<3.13`), [`uv`](https://docs.astral.sh/uv/),
Node 22, and [`pnpm`](https://pnpm.io/) 11. A CUDA GPU (RTX 5090-class) is needed
only to run inference — not for the CPU checks below.

```bash
# API (Python) — torch-free CPU environment
uv python install 3.12
uv sync --frozen --group test-cpu

# WebUI (Node)
cd webui && pnpm install --frozen-lockfile && cd ..
```

## Checks to run before you open a PR

These mirror the CPU-only CI in `.github/workflows/ci.yml`. Please run and pass
them locally first.

```bash
# ── Python (API) ──
uv run ruff check api tests
uv run pytest -m "not gpu"          # CPU suite; excludes GPU-marked tests

# ── WebUI (from the webui/ directory) ──
cd webui
pnpm gen:api && git diff --exit-code lib/api/schema.d.ts   # client types in sync with schemas/openapi.json
pnpm build                          # Next generates types that typecheck needs — build first
pnpm lint
pnpm typecheck
pnpm test
```

GPU inference is a **manual gate** (see `docs/risk_register.md` R-05 and the
release checklist); GPU-marked tests run only with `COSMOS3_ENABLE_GPU_TESTS=1
uv run pytest -m gpu` on supported hardware.

## Pull request guidelines

1. Fork and create a topic branch.
2. Keep changes focused. If you change the OpenAPI schema
   (`schemas/openapi.json`) or the API surface, regenerate the WebUI client types
   (`pnpm gen:api`) and update tests — CI enforces both.
3. **Stage files explicitly** — prefer `git add <path> <path>` over `git add .`,
   so build artifacts, caches, and model weights never enter a commit.
4. Do not commit secrets, tokens, private paths, or model weights. Weights are
   external (see `docs/model_setup.md`); the repo scans for private references.
5. Fill in the pull request template: what changed, why, and which checks you ran.
6. Use clear commit messages (a `type(scope): summary` style is appreciated).

## Claims and evidence

This project keeps runtime claims (GPU, FP8/NVFP4, performance) tied to evidence
or marked as beta limitations — see `docs/evidence_map.md`. If a change affects a
claim in the README or docs, update the evidence accordingly rather than
overstating what is verified.

## Questions

Open a GitHub Discussion or a question-style issue. For anything security-related,
use [SECURITY.md](SECURITY.md).
