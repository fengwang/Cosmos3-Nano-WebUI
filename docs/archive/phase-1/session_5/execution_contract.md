# Session 5 Execution Contract - CPU-Only CI and Test Stabilization

Session: MIG-S5
Risk: medium · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S5-CI`

## Planned file changes

Created:
- `.github/workflows/ci.yml`
- `tests/conftest.py`, `tests/test_private_ref_scan.py`
- `docs/session_5/{brainstorming,proposal,design,tasks,plan,execution_contract}.md`,
  `docs/session_5/specs/{cpu_ci_pipeline,cpu_test_stabilization,gpu_test_isolation,schema_sync_gate,private_reference_scan}.md`,
  `docs/session_5/local_checks.md`
- `docs/session_5/{failure_arbiter (if any),sharded_review,adversarial_verification}.md`
- `docs/eval_corpus/mig_s5_*.md`

Updated:
- `tests/api/test_gen_ipc.py` (F541), `tests/api/test_oracle_adapter_audio.py` (E402 noqa)
- `pyproject.toml` (`test-cpu` group), `uv.lock` (regenerated)
- `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
  `docs/handoff.md`
- `docs/session_5_contract.yaml` (D10 `allowed_files` amendment)

## Allowed blast radius

Permitted (contract `allowed_files` + D10 amendment): `.github/workflows/**`,
`pyproject.toml`, `uv.lock`, `webui/package.json`, `webui/pnpm-lock.yaml`,
`webui/pnpm-workspace.yaml`, `webui/vitest.config.ts`, `webui/playwright.config.ts`,
`tests/**`, `schemas/**`, `docs/session_5/**`, `docs/evidence_map.md`,
`docs/risk_register.md`, and (D10) `docs/handoff.md`, `docs/eval_corpus/**`,
`docs/eval_seed_cases.md`, `docs/session_5_contract.yaml`.

Forbidden (stop if a change seems required): model-weight/media files; Docker
publishing workflows or any secret; `README.md`; vLLM-Omni fork source; runtime
source under `api/**` and `webui/**` product code (editing `tests/**` is allowed;
regenerating `schemas/openapi.json` is allowed only to prove it is unchanged, never
to alter the public API surface — INV-9). No new production dependency (INV-10);
`test-cpu` is torch-free test-only.

## First test to write

The scrub scanner's own unit assertions, written before the scan functions exist
(spec `private_reference_scan`):
```python
# Fixtures built by concatenation so no literal secret-shaped string is committed.
assert scan_text("x", "-----BEGIN " + "OPENSSH PRIVATE KEY-----")  # secret header
assert scan_text("x", "hf_" + "A" * 32)                            # HF token
assert not scan_text("docs/x.md", "/path/to/Cosmos3-Nano-FP8-Blockwise")  # placeholder
assert scan_tree(REPO_ROOT) == []                                  # clean tree
```
`uv run pytest tests/test_private_ref_scan.py` must fail before the functions exist,
then pass once implemented and patterns are tuned to the clean tree. The `F541`/
`E402` fixes are validated by `uv run ruff check api tests` returning exit 0.

## Checks to run after each task

- Python (contract): `uv run ruff check api tests`;
  `uv sync --frozen --group test-cpu` then `uv run pytest -m "not gpu"`.
- Schema sync: `tests/test_openapi.py` (in the pytest run);
  `cd webui && pnpm gen:api && git diff --exit-code lib/api/schema.d.ts`.
- WebUI: `cd webui && pnpm install --frozen-lockfile && pnpm build && pnpm lint &&
  pnpm typecheck && pnpm test`.
- Scrub / provenance regression over this session's own output (R-01,
  `EV-MIG-DOCS-SCRUB`): `uv run python tests/test_private_ref_scan.py` and
  `rg -n -i -e '/home/[a-z]' -e 'hf_[A-Za-z0-9]{20}' -e 'sk-[A-Za-z0-9]{20}' -e 'BEGIN [A-Z ]*PRIVATE KEY' docs/session_5 .github`
  → no match before each commit.
- Workflow sanity: YAML parses; every CI step maps to a locally-passing command.
- GPU guard: throwaway `gpu` test skipped by default, runs under
  `COSMOS3_ENABLE_GPU_TESTS=1`.

## Review axes to run at the end

correctness · security · tests · architecture · performance (per
`docs/agent_workflow/prompts/sharded_review.md`). Each reviewer read-only; reports
severity + evidence (file/line) + violated clause + smallest safe fix + confidence.
Fix only High/Critical; re-run checks after fixes.

## Adversarial verifier brief

Fresh context; sees only `docs/session_5_contract.yaml`, the session diff, and the
evidence — not this conversation. Task: falsify "`GATE-MIG-S5-CI` passes with
CPU-only public CI ready for the beta branch." Specifically attempt to show:
(a) the workflow passes because it skips or does not actually run meaningful tests
(hollow pass); (b) the workflow needs a secret, CUDA, model weights, private
network, or a self-hosted runner (INV-5); (c) a `gpu`-marked test can run or fail in
CPU CI, or a heavy top-level import breaks collection; (d) generated OpenAPI or
`schema.d.ts` can drift without failing CI; (e) the private-reference scan misses a
planted secret or blocks the clean tree with a false positive; (f) a private path,
host, or secret leaked into any session doc; (g) a public API route/request shape
changed (INV-9) or a production dependency was added (INV-10). Any confirmed item
fails the session and is routed through the Failure Arbiter.

## Concrete done condition

`GATE-MIG-S5-CI` is satisfied when all hold, each backed by command evidence:
1. `.github/workflows/ci.yml` exists, triggers on push + PR, is `contents: read`,
   references no secret, and cancels superseded runs.
2. `uv run ruff check api tests` exits 0.
3. `uv run pytest -m "not gpu"` passes with the `test-cpu` group, and the three
   artifact-encoder tests execute (not skipped for `numpy`).
4. WebUI `install --frozen-lockfile → gen:api diff → build → lint → typecheck →
   test` all pass locally; both schema-sync layers are wired into CI.
5. `gpu`-marked tests are skipped off-GPU by `conftest.py` and by `-m "not gpu"`;
   the manual GPU command is documented.
6. `tests/test_private_ref_scan.py` reports zero findings on the clean tree, catches
   a planted secret/weight in unit tests, runs in CI and via CLI.
7. Developer local-check command list documents the CPU-only reproduction.
8. Sharded review has no unresolved High/Critical; adversarial verifier passes.
9. `docs/handoff.md` hands S6/S8 the workflow names, local commands, known skips,
   classified failures, and the still-open R-05.
