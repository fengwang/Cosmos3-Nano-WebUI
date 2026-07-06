# Session 5 Tasks - CPU-Only CI and Test Stabilization

Session: MIG-S5
Derived from: `specs/*.md` (what) + `design.md` (how)

## 1. Baseline fixes and CPU test group

- [ ] 1.1 Fix `F541` in `tests/api/test_gen_ipc.py` (remove the stray `f` prefix on
      the assertion string) — spec `cpu_test_stabilization` (lint-clean).
- [ ] 1.2 Fix `E402` in `tests/api/test_oracle_adapter_audio.py` with an inline
      `# noqa: E402` + one-line reason (stub-before-import is intentional); add no
      global ignore — spec `cpu_test_stabilization`.
- [ ] 1.3 Add `[dependency-groups] test-cpu = ["numpy","pillow","imageio","imageio-ffmpeg"]`
      to `pyproject.toml`; run `uv lock` to regenerate `uv.lock` — spec
      `cpu_test_stabilization`.
- [ ] 1.4 Verify: `uv run ruff check api tests` exits 0; `uv sync --frozen --group
      test-cpu` then `uv run pytest -m "not gpu"` runs the encoder tests (no numpy
      skip) and passes; `torch` absent.

## 2. GPU test isolation

- [ ] 2.1 Add `tests/conftest.py` with `pytest_collection_modifyitems` skipping
      `gpu`-marked items unless `COSMOS3_ENABLE_GPU_TESTS` is truthy; include a
      comment documenting the heavy-import guard convention — spec
      `gpu_test_isolation`.
- [ ] 2.2 Verify with a temporary throwaway `gpu`-marked test: skipped by default,
      runs under `COSMOS3_ENABLE_GPU_TESTS=1`; then delete the throwaway.

## 3. Private reference scan

- [ ] 3.1 Write `tests/test_private_ref_scan.py`: pure `scan(...)` Calculation
      (regex rules + allowed placeholders + self-exclusions), a `pytest` wrapper
      over the controlled surface, and a `__main__` CLI — spec
      `private_reference_scan`.
- [ ] 3.2 Verify: pytest wrapper reports zero findings on the clean tree; unit
      assertions prove a planted key header / `hf_` / `sk-` token and a weight
      extension are caught, and that placeholders + the checklist are not.

## 4. CI workflow

- [ ] 4.1 Establish the WebUI baseline locally: `pnpm install --frozen-lockfile`;
      determine empirically whether `pnpm typecheck` needs a prior `pnpm build`;
      run `gen:api` diff, `build`, `lint`, `typecheck`, `test` — spec
      `cpu_ci_pipeline`, `schema_sync_gate`. Classify any failure (Failure Arbiter).
- [ ] 4.2 Write `.github/workflows/ci.yml`: `python` job (setup-uv, py3.12, `uv sync
      --frozen --group test-cpu`, ruff, `pytest -m "not gpu"`) + `webui` job
      (pnpm 11.3.0, node 22, frozen install, gen:api diff, build, lint, typecheck,
      test); `push`+`pull_request`, `permissions: contents: read`, `concurrency`,
      `NEXT_TELEMETRY_DISABLED=1`, no secrets — spec `cpu_ci_pipeline`.
- [ ] 4.3 Validate the workflow structurally (YAML parse; optional `actionlint`;
      confirm every CI step maps to a locally-passing command).

## 5. Developer command list

- [ ] 5.1 Write the local-check command list under `docs/session_5/` (Python + WebUI
      commands mirroring CI, plus the manual GPU command and the scrub CLI) — specs
      `cpu_ci_pipeline`, `gpu_test_isolation`.

## 6. Verification and review

- [ ] 6.1 Run all contract deterministic checks; classify any failure via the
      Failure Arbiter; save `docs/session_5/failure_arbiter.md` if any.
- [ ] 6.2 Sharded review (correctness / security / tests / architecture /
      performance); save `docs/session_5/sharded_review.md`; fix only High/Critical;
      re-check.
- [ ] 6.3 Adversarial verification (fresh context; contract + diff + evidence only);
      save `docs/session_5/adversarial_verification.md`.

## 7. Close

- [ ] 7.1 Amend `docs/session_5_contract.yaml` `allowed_files` (D10:
      `docs/handoff.md`, `docs/eval_corpus/**`, `docs/eval_seed_cases.md`).
- [ ] 7.2 Update `docs/evidence_map.md`, `docs/risk_register.md` (R-05/R-10/R-14),
      `docs/eval_seed_cases.md`; add `docs/eval_corpus/` seeds.
- [ ] 7.3 Verify the done condition (`GATE-MIG-S5-CI`); write/update
      `docs/handoff.md`; state remaining risks and next-session warnings.

## Ordering / dependencies

1 → 2 → 3 unblock the Python job; 4.1 must precede 4.2 (baseline informs the
workflow); 4 depends on 1–3 being green. 5 documents 1–4. 6 runs after 1–5. 7
closes after 6. The contract amendment (7.1) is prerequisite to writing
`docs/handoff.md`/`docs/eval_corpus/**` (7.2–7.3) but may be committed once the
need is confirmed.
