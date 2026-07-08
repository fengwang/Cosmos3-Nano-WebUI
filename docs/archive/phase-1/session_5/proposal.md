# Session 5 Proposal - CPU-Only CI and Test Stabilization

Date: 2026-07-07
Session: MIG-S5
Status: Derived from approved brainstorming

## Motivation

The public beta needs a repeatable quality gate that outside contributors can run
without model weights, CUDA, private network access, or self-hosted runners
(PRD §3.10, INV-5, `GATE-MIG-S5-CI`). Sessions 1–4 produced the docs pack, the
pinned vLLM-Omni fork, the curated API/WebUI import, and the checkpoint-setup
contract, but there is still **no `.github/` workflow** and the imported test
commands have never been run as a public gate. A grounded baseline shows exactly
one broken deterministic check — `ruff check tests` fails with two errors — while
`pytest -m "not gpu"` already passes torch-free. Session 5 adds the CPU workflows,
stabilizes the public test commands, and hardens against the contract's four
adversarial cases (hollow test pass, hidden secret requirement, GPU import failure
during CPU collection, silent schema drift).

## Agreed Changes

- Add a single `.github/workflows/ci.yml` (INV-5, no secrets, `contents: read`,
  concurrency cancel) with two parallel `ubuntu-latest` jobs: **python** and
  **webui**.
- **Python job**: `uv`-provisioned Python 3.12, `uv sync --frozen --group
  test-cpu` (torch-free), `ruff check api tests`, `pytest -m "not gpu"`.
- **WebUI job**: `pnpm@11.3.0` + Node 22, `pnpm install --frozen-lockfile`,
  `gen:api` + `git diff --exit-code lib/api/schema.d.ts`, `next build`, `lint`,
  `typecheck`, `test`. Build-before-typecheck confirmed empirically.
- Fix the two `ruff` errors in `tests/` (`F541` stray f-string;
  `E402` intentional stub-before-import → inline `# noqa: E402`).
- Add a torch-free `[dependency-groups] test-cpu` (`numpy`, `pillow`, `imageio`,
  `imageio-ffmpeg`, `safetensors`) so the currently-skipped artifact-encoder and
  checkpoint-writer tests actually execute in CI (anti-hollow-pass); regenerate
  `uv.lock`.
- Add `tests/conftest.py` that auto-skips `@pytest.mark.gpu` tests unless
  `COSMOS3_ENABLE_GPU_TESTS` is set, and keep `-m "not gpu"` in CI; document the
  "gpu modules must guard heavy imports" convention and the manual GPU command.
- Add `tests/test_private_ref_scan.py`: a pure scan function + pytest wrapper +
  `__main__` CLI implementing the S1 fallback private-reference/secret pattern,
  scoped to avoid matching its own definition (`EV-MIG-SCRUB-COMMAND-SANITY`).
- Document the developer local-check command set (mirrors CI exactly).
- Amend `session_5_contract.yaml` `allowed_files` to add `docs/handoff.md`,
  `docs/eval_corpus/**`, `docs/eval_seed_cases.md` (Session End Protocol; S4 FA-4
  precedent).
- Update `docs/evidence_map.md` and `docs/risk_register.md` (R-05, R-10, R-14).
- Commit at clean checkpoints on `session-5`; do not push.

## Capabilities

### New Capabilities

1. **CPU CI Pipeline** (`cpu_ci_pipeline`)
   - A CPU-only GitHub Actions workflow runs the public Python and WebUI checks on
     `ubuntu-latest` without CUDA, model weights, secrets, private network access,
     or self-hosted runners, and the identical checks are reproducible locally from
     a documented command set.

2. **CPU Test Stabilization** (`cpu_test_stabilization`)
   - The Python suite is lint-clean and collects torch-free, and the previously
     `numpy`-skipped artifact-encoder tests execute under a torch-free CPU test
     dependency group, so a green run reflects meaningful coverage rather than mass
     skips (`EV-MIG-PY-UNIT`, `EV-MIG-IMPORT-COMPLETE`).

3. **GPU Test Isolation** (`gpu_test_isolation`)
   - GPU-only tests are separated from the CPU gate: a collection hook skips
     `@pytest.mark.gpu` tests off-GPU, CI filters them with `-m "not gpu"`, heavy
     imports are guarded so collection never fails, and a manual GPU command is
     documented for S8.

4. **Schema Sync Gate** (`schema_sync_gate`)
   - CI fails if the FastAPI app drifts from committed `schemas/openapi.json`
     (`tests/test_openapi.py`) or if `webui/lib/api/schema.d.ts` drifts from
     `openapi.json` (`pnpm gen:api` + `git diff --exit-code`) — both torch-free
     (`EV-MIG-SCHEMA-SYNC`).

5. **Private Reference Scan** (`private_reference_scan`)
   - A committed, testable scan detects private paths, hosts, secrets/tokens, and
     committed weight/media files across the change-controlled surface, ignoring
     allowed placeholders and its own pattern definition, and runs in CI and
     locally (INV-1, R-01, R-14, `EV-MIG-SCRUB`, `EV-MIG-DOCS-SCRUB`).

### Modified Capabilities

None. Session 5 adds CI and test-harness capabilities. It does not change public
API route names or request shapes (INV-9), production dependencies (the `test-cpu`
group is CPU test-only, torch-free, and reuses pins already declared in the
`oracle` extra — INV-10), or the WebUI product surface.

## Impact

Affected files (all within the S5 blast radius, one contract amendment):

- New: `.github/workflows/ci.yml`, `tests/conftest.py`,
  `tests/test_private_ref_scan.py`.
- Edited: `tests/api/test_gen_ipc.py` (F541), `tests/api/test_oracle_adapter_audio.py`
  (E402 noqa), `pyproject.toml` (+`test-cpu` group), `uv.lock` (regenerated).
- Docs: `docs/session_5/**` (this refining pack + review/verify/failure-arbiter +
  local-checks list), `docs/evidence_map.md`, `docs/risk_register.md`,
  `docs/eval_seed_cases.md`, `docs/eval_corpus/**`, `docs/handoff.md`.
- Contract: `docs/session_5_contract.yaml` `allowed_files` amendment (D10).

Affected code / APIs / systems: no runtime source, schema content, or public API
behavior changes. `openapi.json` is regenerated only to prove it is unchanged.

Dependency impact: `test-cpu` group adds `numpy`, `pillow`, `imageio`,
`imageio-ffmpeg`, `safetensors` (torch-free, CPU test-only; versions already
present in the `oracle` extra). No production dependency and no third-party GitHub Action beyond
the pinned `astral-sh/setup-uv`, `pnpm/action-setup`, `actions/setup-node`,
`actions/checkout`.

Handoff impact: S6 (Docker) adds `EV-MIG-COMPOSE-RENDER` render checks once
`deploy/` exists; S8 consumes the manual GPU command and the still-open R-05
(CPU-green-while-GPU-broken).
