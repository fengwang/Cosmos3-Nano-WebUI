# Session 3 Tasks - Curated WebUI/API Source Import and Scrub

Session: MIG-S3
Source of truth: `docs/session_3/specs/*` (WHAT), `docs/session_3/design.md` (HOW)

Tasks are dependency-ordered. Each is verifiable by the check in its line or by the
referenced spec scenario. Checks use `rtk` per the contract; where `$PRIVATE_REF_PATTERN`
is unset, the Session 3 pattern from `private_reference_scrub.md` is used.

## 1. Baseline And Allowlist

- [ ] 1.1 Record baseline scans on the empty repo (private-ref, artifact, legacy) and the expected pre-import `compileall api` failure.
- [ ] 1.2 Generate the include/exclude/defer allowlist from the private repo's `git ls-files` (api minus trtllm; webui; schemas; tools; CPU-safe tests; root manifests; defer deploy; exclude submodules/.gitmodules/.github/docs/README).
- [ ] 1.3 Write `docs/session_3/import_manifest.md` with INCLUDED / EXCLUDED / DEFERRED dispositions and reasons.

## 2. Import API And Scrub (spec: curated_source_import, legacy_dependency_exclusion)

- [ ] 2.1 Import root manifests `pyproject.toml` and `uv.lock`; verify no private source/index reference.
- [ ] 2.2 Import `api/**` except `api/engines/trtllm/**`.
- [ ] 2.3 Scrub kept API source: rephrase the `submodules/vllm/...` comment in `api/engines/vllm/reasoner_preflight.py` to reference the public vLLM-Omni fork.
- [ ] 2.4 Verify: `rtk python -m compileall api` exits 0 and no kept `api/` file imports `engines.trtllm`.

## 3. Import Schemas And Tools (spec: curated_source_import, private_reference_scrub)

- [ ] 3.1 Import `schemas/openapi.json` and `schemas/README.md`.
- [ ] 3.2 Import `tools/checkpoint_prep/**`; env-drive `_BF16_BASE_REF` in `copy_shared.py` (default `/data/models/Cosmos3-Nano`).
- [ ] 3.3 Verify: `rtk python -m compileall tools` exits 0.

## 4. Import CPU-Safe Tests (spec: curated_source_import, cpu_source_smoke)

- [ ] 4.1 Import CPU-safe tests: `tests/api/` (non-gpu), `tests/checkpoint_prep/`, top-level `test_*.py` minus `*_gpu.py` and `test_trtllm_contract.py`. Exclude `tests/equivalence/`, `tests/e2e/`, `tests/bench/`, `tests/deploy/`.
- [ ] 4.2 Verify no kept test imports `engines.trtllm` or the `equivalence` harness; drop or fix any that do.
- [ ] 4.3 Verify: `PYTHONPATH=api rtk python -c "import app.main"` exits 0; `rtk python -m pytest -q -m "not gpu"` passes or failures are classified.

## 5. Import WebUI (spec: curated_source_import, private_reference_scrub)

- [ ] 5.1 Import `webui/**` tracked files (source, `design-system/`, `components/`, `lib/` + `*.test.ts`, `public/urdf/`, configs, `package.json`, `pnpm-lock.yaml`); ensure no `node_modules`/build output.
- [ ] 5.2 Verify WebUI structure + private-reference-clean; run `lint`/`typecheck`/`vitest` if node+network available, else classify ENVIRONMENT and hand to S5.

## 6. Full Checks And Scrub Report (spec: private_reference_scrub, cpu_source_smoke)

- [ ] 6.1 Run all scans over the imported tree: private-ref, weight/media extension, archive, cache/node_modules, submodule/legacy. All clean.
- [ ] 6.2 Schema-sync: regenerate OpenAPI from the app and compare to `schemas/openapi.json`; disposition any diff.
- [ ] 6.3 Write `docs/session_3/scrub_report.md` and the source smoke evidence (commands + results + classifications).

## 7. Review, Verification, Handoff

- [ ] 7.1 Sharded review (correctness, security, tests, architecture, performance); dedupe; fix only High/Critical; re-check. Save `docs/session_3/sharded_review.md`.
- [ ] 7.2 Adversarial verification against `GATE-MIG-S3-IMPORT`; classify any failure. Save `docs/session_3/adversarial_verification.md`.
- [ ] 7.3 Update `docs/evidence_map.md` and `docs/risk_register.md`; write `docs/handoff.md`; add eval seeds under `docs/eval_corpus/`; update `docs/eval_seed_cases.md`.
