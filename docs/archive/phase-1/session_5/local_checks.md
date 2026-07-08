# Session 5 - Developer Local Checks

Session: MIG-S5 · Gate: `GATE-MIG-S5-CI`

These commands reproduce the CPU-only CI (`.github/workflows/ci.yml`) locally. None
require a secret, a GPU, model weights, or private network access. The host `python3`
may be newer than the project's pin, so all Python commands go through `uv`, which
provisions Python 3.12.

## Python (mirrors the `python` CI job)

```bash
# provision the pinned interpreter + torch-free deps (core + dev + test-cpu)
uv python install 3.12
uv sync --frozen --group test-cpu

# lint + CPU tests (the pytest run also executes the app<->openapi drift check in
# tests/test_openapi.py and the private-reference scan in tests/test_private_ref_scan.py)
uv run ruff check api tests
uv run pytest -m "not gpu"
```

Expected: `ruff` exits 0; `pytest` reports `471 passed` from the suite plus the
scanner's own unit tests (479 passed, 0 skipped total), 0 failures. The `test-cpu`
group (`numpy`, `pillow`, `imageio`, `imageio-ffmpeg`, `safetensors`) makes the
image/video artifact-encoder and checkpoint-writer tests execute instead of skip.

## WebUI (mirrors the `webui` CI job)

```bash
cd webui
pnpm install --frozen-lockfile

# schema sync: regenerate client types from schemas/openapi.json; fail on drift
pnpm gen:api && git diff --exit-code lib/api/schema.d.ts

# build FIRST: Next generates .next/types (incl. CSS-module *.d.ts) that
# `tsc --noEmit` needs; this also validates the production bundle
pnpm build
pnpm lint
pnpm typecheck
pnpm test
```

Expected: all steps exit 0; `vitest` reports `39` files / `208` tests passed.
Note: `pnpm typecheck` FAILS if run before `pnpm build` (missing CSS-module type
declarations) — always build first. CI pins Node 22; a newer local Node works for
these checks (the lockfile, not the Node minor, determines resolution).

## Private-reference / secret scan (standalone)

```bash
# same scan the pytest run performs, as a CLI (exit 1 == findings)
uv run python tests/test_private_ref_scan.py
```

The committed scan covers high-confidence secret *values*, private absolute paths,
and committed weight/media files across `.github`, `api`, `webui`, `tests`,
`schemas`, `docs`. The broader lexical name-assignment scan from
`docs/session_1/scrub_checklist.md` remains a human-reviewed release-gate step (S8).

## Manual GPU tests (NOT part of CPU CI — S8 release gate)

GPU-marked tests are skipped on the CPU loop. To run them on real hardware
(RTX 5090):

```bash
COSMOS3_ENABLE_GPU_TESTS=1 uv run pytest -m gpu
```

This is a manual release gate (`R-05`: CPU CI cannot prove GPU inference works).
No GPU test exists in the imported CPU-safe suite yet; a future GPU-only module
MUST guard heavy imports (e.g. `pytest.importorskip("torch")`) so collection never
fails on a CPU runner.
