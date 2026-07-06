# Session Handoff

## State Snapshot

- Session: MIG-S3, Curated WebUI/API Source Import and Scrub
- Branch: WebUI repo `session-3` (local commits only; not pushed)
- Last commit: `docs(s3): adversarial verification, evidence/risk, handoff, eval seeds`
- Changed files:
  - Imported source (296 files): `api/**` (except `api/engines/trtllm/`), `webui/**`,
    `schemas/{openapi.json,README.md}`, `tools/checkpoint_prep/**`, CPU-safe `tests/**`,
    `pyproject.toml`, `uv.lock`
  - Docs: `docs/session_3/**` (refining pack + import_manifest + scrub_report +
    source_smoke + failure_arbiter + sharded_review + adversarial_verification),
    `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
    `docs/eval_corpus/mig_s3_*.md`, `docs/handoff.md`
- Checks run (torch-free Python 3.12 uv venv; node 26 / pnpm 11.3.0):
  - `python -m compileall api` and `compileall tools` = exit 0
  - torch-free `PYTHONPATH=api python -c "import app.main"` = OK (FastAPI builds)
  - `pytest -m "not gpu"` = 467 passed, 3 skipped (numpy absent), 0 failed
  - OpenAPI schema-sync (`test_committed_openapi_matches_live_app`) = pass; regen byte-identical
  - Private-reference / weight-media / archive / cache / legacy-submodule scans =
    clean over source AND `docs/session_3/**`; `.gitmodules` absent
  - WebUI (best-effort): `pnpm install` OK, `tsc` typecheck OK (after generated
    `next-env.d.ts`), `vitest` 208 passed, `eslint` clean
  - Sharded review (5 axes) + fresh-context adversarial verifier = PASS
- Checks not run:
  - GPU inference / VRAM / performance (RTX 5090) — deferred to `MIG-S8`
  - CPU-only GitHub Actions wiring — `MIG-S5`
  - HF checkpoint file-layout/runtime probes — `MIG-S4`
  - Docker/Compose build and render — `MIG-S6`
  - Live WebUI `next build` and Playwright e2e — `MIG-S5`
- Current status: `GATE-MIG-S3-IMPORT` is satisfied. Curated, scrubbed public source
  tree is present and CPU-verified; all deterministic scans clean; one HIGH docs-leak
  finding (FA-6) was caught by review and fixed.

## Narrative Context

Session 3 imported the API and WebUI source from the owner-provided private repo into
the previously-empty public repo, using a manifest-driven allowlist copy plus targeted
scrub. The TensorRT-LLM engine, three legacy git submodules, `.gitmodules` (a private
host), GPU/equivalence/e2e tests, and all of `deploy/` were excluded or deferred. The
imported tree compiles, imports torch-free, and passes its CPU test suite; the OpenAPI
schema is in sync. Sharded review caught private values that had leaked into this
session's own planning docs (a recurrence of the MIG-S2 defect); they were redacted to
descriptor language, and a fresh-context verifier confirmed the done condition.

## Decision Log

| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| Import method | Manifest-driven allowlist copy + targeted scrub | Full-tree copy then prune; rewrite from scratch | Auditable diff; avoids "broad import hides leaks"; keeps proven code | `docs/session_3/design.md` D1 |
| `api/engines/trtllm/` | Exclude (unreachable from server; no proven public need) | Keep scrubbed | Clean-design; removes "legacy TensorRT reachable" case | Q_C; `session_3_contract.yaml` |
| `/data/models` | Keep as documented container-mount convention; real dirs via `COSMOS3_*` env | Replace everywhere | Not a home/secret; preserves trust-boundary test semantics | Q_A; design.md D4 |
| Test scope | CPU-safe only; exclude gpu/equivalence/e2e/bench/deploy | Import GPU tests scrubbed | CPU-only S3 scope; GPU is the `MIG-S8` gate | Q_B; design.md D5 |
| `deploy/` | Defer entire tree to `MIG-S6` | Import non-Docker helpers now | Docker/Compose is S6; nothing cleanly non-Docker | design.md D6 |
| Docs private values | Redact to descriptor language / generic detectors | Name the owner-provided path/host/repo verbatim | INV-1; MIG-S2 eval precedent | FA-6; `docs/eval_corpus/mig_s2_private_source_scrub.md` |

## Next Priority Queue

1. `MIG-S4`: probe FP8/NVFP4 Hugging Face checkpoint metadata, file layout, and
   compatibility against the imported loaders (`api/engines/diffusers_*`) and the
   Session 2 pinned fork.
2. `MIG-S5`: stand up CPU-only GitHub Actions from the imported tree — Python
   (`compileall`, `import app.main`, `pytest -m "not gpu"`), OpenAPI schema-sync
   (`EV-MIG-SCHEMA-SYNC`), WebUI (`pnpm install/lint/typecheck/vitest`, with
   `next build` to generate `next-env.d.ts` before `tsc`), and the pre-existing
   test-coverage gaps below. Add the `EV-MIG-DOCS-SCRUB` and `EV-MIG-IMPORT-COMPLETE`
   checks.
3. `MIG-S6`: import + build Docker/Compose from the pinned vLLM-Omni fork with external
   checkpoint mounts; this is where `deploy/**` lands.

## Warnings And Gotchas

- Environment issues:
  - Host Python is 3.14 (project needs 3.12,<3.13); use a `uv` venv for checks.
  - WebUI `tsc --noEmit` needs the Next-generated `next-env.d.ts` (gitignored);
    run `next build` first, or `tsc` reports spurious `TS2307` on `*.module.css`.
    Classified ENVIRONMENT (FA-3), routed to `MIG-S5`.
- Known failing/weak tests (pre-existing, imported verbatim; routed to `MIG-S5`):
  - Torch-free `count_tokens` heuristic fallback (reasoning cap) is unasserted.
  - `tools/checkpoint_prep/safetensors_io.py:parse_header` only has numpy-skipped
    coverage; near-tautology at `tests/test_vllm_omni_client.py:76`; unpinned
    `pytest.raises(ImportError)` at `tests/api/test_reasoner_preflight_unit.py`.
  - Trailing blank line at `tests/checkpoint_prep/test_copy_shared_integration.py:170`
    (ruff will normalize).
- Deferred risks: HF checkpoint compatibility (S4), CI (S5), Docker build (S6), GPU
  runtime/VRAM/performance (S8) all remain unverified.
- Files future sessions must not casually edit: imported public API route names and
  request shapes (INV-9), `schemas/openapi.json` (regenerate via
  `python -m app.openapi_export`, don't hand-edit), `pyproject.toml`/`uv.lock` pins.
  Do not import `submodules/`, `.gitmodules`, `api/engines/trtllm/`, `.github/**`, or
  private `docs/**`. Do not name private paths/hosts/repos in public docs.

## Eval Seeds

- Missed check (caught by review, not by the first scan): the session's own
  `docs/session_3/**` re-leaked private values (path/host/repo) —
  `docs/eval_corpus/mig_s3_docs_private_scrub_recurrence.md` (extends `EV-MIG-DOCS-SCRUB`).
- New regression test candidate: curated-import completeness / no hollow pass —
  `docs/eval_corpus/mig_s3_import_completeness.md` (extends `EV-MIG-IMPORT-COMPLETE`).
- Instruction update candidate: import/scrub sessions MUST run the private-value
  regression over their OWN `docs/session_*/**` output before commit, and prefer
  descriptor language over quoting owner-provided private paths/hosts verbatim.
