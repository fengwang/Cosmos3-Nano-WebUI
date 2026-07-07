# Eval Seed Cases - GitHub Migration Public Beta

Date: 2026-07-06

These cases seed deterministic checks and manual release gates for the migration.
They avoid private paths and assume checkpoints are downloaded or mounted from
public Hugging Face repos.

## Public Checkpoint IDs

- FP8 (generation): `wfen/Cosmos3-Nano-FP8-Blockwise`
- NVFP4 (generation): `wfen/Cosmos3-Nano-NVFP4-Blockwise`
- BF16 base (reasoner + action/forward_dynamics): `nvidia/Cosmos3-Nano` (public, ungated)

Operators set local paths with the actual runtime environment variables (authoritative
list + defaults in `docs/model_setup.md`), e.g.:

- `COSMOS3_MODEL_DIR=/path/to/Cosmos3-Nano-FP8-Blockwise` with `COSMOS3_CHECKPOINT_LABEL=fp8`
- `COSMOS3_REASONER_MODEL_DIR=/path/to/Cosmos3-Nano` and
  `COSMOS3_BASE_ACTION_DIR=/path/to/Cosmos3-Nano/transformer`

## Deterministic Public Checks

| ID | Purpose | Inputs | Expected properties | Gate |
|---|---|---|---|---|
| EV-MIG-REPO-TREE | Confirm public repo shape after import. | `git status`, `rg --files` | Runtime source, tests, schemas, deploy files, and docs are present; archives/caches/model weights are absent. | MIG-S3 |
| EV-MIG-SCRUB | Detect private references. | Recursive `rg` patterns for private hosts, private absolute paths, codenames, secrets, and model-weight paths. | No matches outside explicitly allowed placeholder examples. | MIG-S1, MIG-S3, MIG-S7, MIG-S8 |
| EV-MIG-SCRUB-COMMAND-SANITY | Confirm scrub checks search the intended surface and do not match their own documentation. | `docs/session_1/scrub_checklist.md`, fallback private-reference scan, and `rg --files` path scans. | Content scans are used for private references; file-path scans are used for extensions, caches, archives, artifact folders, and legacy submodules; documented regex examples do not create false release blockers. | MIG-S1, MIG-S3, MIG-S7, MIG-S8 |
| EV-MIG-DOCS-SCRUB | Detect private references in the session's OWN committed docs, not only the imported source. | `docs/session_*/**` (incl. `probes/` outputs), `docs/model_setup.md`, `docs/evidence_map.md`, `docs/risk_register.md`, `docs/handoff.md` | No real private path/host/codename/repo/dev-variant; policy/descriptor language and generic detectors allowed. See `docs/eval_corpus/mig_s3_docs_private_scrub_recurrence.md`. | MIG-S3, MIG-S4, MIG-S7, MIG-S8 |
| EV-MIG-IMPORT-COMPLETE | Prove the curated import graph is complete (no hollow test pass). | `compileall api`, torch-free `import app.main`, `pytest -m "not gpu"`, excluded-module import grep | Compile+import succeed; suite passes and FAILS under an inverted core gate; no kept file imports excluded modules (`engines.trtllm`, `equivalence`). See `docs/eval_corpus/mig_s3_import_completeness.md`. | MIG-S3, MIG-S5 |
| EV-MIG-VLLM-FORK | Confirm vLLM-Omni public pin. | GitHub fork remote and pinned commit/tag. | Pinned commit exists publicly and contains the Cosmos3 patch line selected by `MIG-S2`. | MIG-S2 |
| EV-MIG-HF-FP8-METADATA | Verify FP8 public checkpoint metadata + loader compatibility. | HF repo ID, revision, license, file listing, model card, `quantization_config.json` recipe (SHA-gated), loader contract. | Reachable; revision `4e181f99…` (ls-remote == HfApi); license `openmdw-1.0`; self-contained; in-process oracle recipe drift (D1) documented. See `docs/session_4/hf_verification.md`, `docs/eval_corpus/mig_s4_nvfp4_loader_layout_drift.md`. | MIG-S4 |
| EV-MIG-HF-NVFP4-METADATA | Verify NVFP4 public checkpoint metadata + loader compatibility. | HF repo ID, revision, license, file listing, model card, transformer layout. | Reachable; revision `b5c9332e…`; license `openmdw-1.0`; 62-byte stub card (D4); NVFP4 layout not loadable by in-process oracle (D1); declared base `nvidia/Cosmos3-Nano` public (D2). See `docs/session_4/drift_report.md`, `docs/eval_corpus/mig_s4_base_model_publication_premise.md`. | MIG-S4 |
| EV-MIG-SCHEMA-SYNC | Confirm OpenAPI and generated client types match. | `schemas/openapi.json`, WebUI generated types. | Schema export and generated TypeScript types are in sync. Two layers wired + proven to fail on drift (`MIG-S5`): `tests/test_openapi.py` (app→`openapi.json`) and `pnpm gen:api` + `git diff --exit-code lib/api/schema.d.ts` (`openapi.json`→types). | MIG-S5 |
| EV-MIG-PY-UNIT | Confirm Python CPU tests. | API tests that do not require CUDA or model weights. | Tests pass in GitHub Actions and local CPU environment. `MIG-S5`: `uv run pytest -m "not gpu"` = 485 passed / 0 skipped (torch-free `--group test-cpu`); `ruff check api tests` = 0; CI job in `.github/workflows/ci.yml`. | MIG-S5 |
| EV-MIG-WEBUI-UNIT | Confirm WebUI CPU tests. | Lint, typecheck, Vitest, selected Playwright stub tests. | Tests pass without model weights or CUDA. `MIG-S5`: `pnpm build`→`lint`→`typecheck`→`test` (vitest 208 passed / 39 files) locally; CI `webui` job. Playwright e2e deferred (not in CPU CI). | MIG-S5 |
| EV-MIG-COMPOSE-RENDER | Confirm Docker/Compose public config. | Compose files and env examples. | Compose renders with no private paths, no baked weights, and configurable checkpoint mounts. **Satisfied (`MIG-S6`):** `docker compose -f deploy/docker-compose.{fp8,nvfp4}.yml config` = exit 0 / 0-byte stderr / correct label; weight-copy `rg` over `deploy/` clean; `tests/test_private_ref_scan.py` clean; lean api (torch-free) + webui `docker build` = exit 0. vLLM-Omni pinned by immutable commit `697035018b70…`; its image build + GPU inference deferred to `MIG-S8`. Workflow seeds: `docs/eval_corpus/mig_s6_compose_env_projectdir.md`, `…reasoning_build_missing_dep.md`, `…scan_doc_selfmatch.md`. | MIG-S6 |
| EV-MIG-README-LINKS | Confirm public docs links. | README, docs, issue templates. | Internal links and public external links resolve or are clearly marked. **Satisfied (`MIG-S7`):** all 10 `README.md` relative link/`src` targets tracked (`git ls-files`), anchors match headings; the CI badge + `security/policy`/`discussions` links resolve post-publish (at-publish item in `docs/release_checklist.md`). | MIG-S7 |
| EV-MIG-LICENSE-HYGIENE | Confirm hygiene files. | `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue/PR templates, `docs/release_checklist.md`. | Files exist and match MIT/public-beta scope: MIT scoped to repo code (weights `openmdw-1.0`/`other`); `SECURITY.md` uses private reporting (no public-issue disclosure); templates request no sensitive data (`blank_issues_enabled:false`). **Satisfied (`MIG-S7`)**; also landed the X-1 auth fix (WebUI→`X-API-Key`, vitest 209) + `.gitignore` hardening. Workflow seeds: `docs/eval_corpus/mig_s7_review_injection_rubber_stamp.md`, `…forbidden_claims_scope.md`, `…stale_sibling_comment_after_fix.md`. | MIG-S7 |

## MIG-S8 re-confirmation (2026-07-07)

The deterministic cases above were re-run green on `session-8` for the release gate:
`EV-MIG-SCRUB` / `-SCRUB-COMMAND-SANITY` / `-DOCS-SCRUB` (committed scanner + broad-scan
human gate clean), `EV-MIG-PY-UNIT` (`pytest -m "not gpu"` = 485 passed), `EV-MIG-WEBUI-UNIT`
(vitest 209), `EV-MIG-SCHEMA-SYNC` (in the pytest run), `EV-MIG-COMPOSE-RENDER` (fp8+nvfp4
`config` exit 0 / 0-byte stderr). Evidence: `docs/session_8/outputs/deterministic_checks.md`.
`EV-MIG-REPO-TREE`, `EV-MIG-IMPORT-COMPLETE`, `EV-MIG-VLLM-FORK`, `EV-MIG-HF-*`,
`EV-MIG-README-LINKS`, `EV-MIG-LICENSE-HYGIENE` remain satisfied from their owning sessions.

## Manual GPU Release Gates

Manual GPU cases are required before public beta GO unless `MIG-S8` explicitly
marks a case beta-limited.

**`MIG-S8` status (2026-07-07):** every case below is **NOT-YET-RUN** and is marked
**beta-limited** (owner decision to defer GPU). They are the standing manual gate for a
post-publish GPU session. A valid run MUST use vLLM-Omni commit
`697035018b70cef76b974a909d23371a9984c3f2` and checkpoint revisions FP8
`4e181f996abf03f3425298ef692e6e5e56fd46a4` / NVFP4
`b5c9332efbaefa72c99890b1b1150da12ca9256c` (otherwise the evidence is invalid); see
`docs/session_8/outputs/gate_record.md`.

| ID | Purpose | Checkpoint | Request shape | Expected properties | Gate |
|---|---|---|---|---|---|
| EV-MIG-GPU-FP8-T2V | FP8 text-to-video smoke. | FP8 | Short prompt, low frame count, documented seed. | Valid video artifact; metadata records frames, fps, dimensions, vLLM-Omni commit, and checkpoint revision. | MIG-S8 |
| EV-MIG-GPU-FP8-T2V-AUDIO | FP8 text-to-video with audio smoke. | FP8 | Prompt with audio-enabled mode if supported by public artifact. | Valid video/audio artifact or documented beta limitation. | MIG-S8 |
| EV-MIG-GPU-FP8-I2V | FP8 image-to-video smoke. | FP8 | Public or generated test image plus prompt. | Valid video artifact or documented beta limitation. | MIG-S8 |
| EV-MIG-GPU-FP8-T2I | FP8 text-to-image smoke. | FP8 | Short prompt, documented seed. | Valid image artifact or documented beta limitation. | MIG-S8 |
| EV-MIG-GPU-FP8-FD | FP8 forward dynamics smoke. | FP8 | Public test first frame and action chunk. | Valid rollout artifact or documented beta limitation. | MIG-S8 |
| EV-MIG-GPU-NVFP4-SURFACE | NVFP4 full-surface smoke. | NVFP4 | Same modes as FP8 where supported. | All supported modes pass or beta limitations are recorded. | MIG-S8 |
| EV-MIG-GPU-REASONING | Reasoning smoke. | Configured reasoning source | Short and long prompts. | Coherent response; no artificial short cap; errors are typed and documented. | MIG-S8 |
| EV-MIG-GPU-JOBS-SSE | Jobs and SSE behavior. | Either checkpoint | Async generation request observed through WebUI. | Progress/events reach terminal state; cancellation works. | MIG-S8 |
| EV-MIG-GPU-ARTIFACTS | Artifact and history views. | Either checkpoint | Completed generation job. | Artifact paths are contained, downloadable, and visible in WebUI history. | MIG-S8 |

## Evidence Fields

For every manual GPU case, record:

- hardware and driver/CUDA context when available
- WebUI repo commit
- vLLM-Omni fork commit or tag
- checkpoint repo ID and revision
- request mode, prompt or fixture name, dimensions, frames, fps, steps, seed
- artifact path, dimensions, streams, duration, and pass/fail result
- known limitation if the case is not passed
