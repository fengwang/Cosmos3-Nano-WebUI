# Session 3 Execution Contract

Date: 2026-07-06
Session: MIG-S3
Risk: high
Status: Active before implementation

## Planned File Changes

Created by curated import (from `the owner-provided private source repo`):

- `api/**` except `api/engines/trtllm/**`
- `webui/**` (tracked files; no `node_modules`/`.next`/build output)
- `schemas/openapi.json`, `schemas/README.md`
- `tools/checkpoint_prep/**`
- `tests/**` CPU-safe subset (excludes `equivalence/`, `e2e/`, `bench/`, `deploy/`, `*_gpu.py`, `test_trtllm_contract.py`)
- `pyproject.toml`, `uv.lock`

Scrub edits (in imported files):

- `api/engines/vllm/reasoner_preflight.py` - remove the `submodules/vllm/...` comment path.
- `tools/checkpoint_prep/copy_shared.py` - env-drive `_BF16_BASE_REF`.

Docs:

- `docs/session_3/**` (refining pack + `import_manifest.md` + `scrub_report.md` + smoke evidence + `failure_arbiter.md` + `sharded_review.md` + `adversarial_verification.md`)
- `docs/evidence_map.md`, `docs/risk_register.md`
- `docs/handoff.md` (Session End Protocol)
- `docs/eval_corpus/**`, `docs/eval_seed_cases.md` (if an issue is caught/missed)

## Allowed Blast Radius

Allowed by `docs/session_3_contract.yaml`:

- `api/**`, `webui/**`, `schemas/**`, `tests/**`, `tools/**`, `deploy/**` (deploy deferred, not edited)
- `pyproject.toml`, `uv.lock`, webui lockfiles
- `docs/session_3/**`, `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`

Lifecycle-authorized additions:

- `docs/handoff.md`, `docs/eval_corpus/**`

Forbidden (must stop if required):

- `submodules/vllm/**`, `submodules/TensorRT-LLM/**`, `submodules/vllm-omni/**`, `.gitmodules`
- `.github/**`, `README.md`
- model weight files, generated media, private archive/evidence folders, private `docs/**`

## First Test To Write Or Identify

```bash
rtk python -m compileall api
```

Before import this fails (no `api/`). It is the first spec-derived check
(`cpu_source_smoke` -> "compileall passes"). Task 2 imports the smallest API set to
make it exit 0, followed by the torch-free `import app.main` completeness check.

## Checks After Each Task

Planning / every task:

```bash
rtk git status --short --branch
rtk git diff --check
```

Task 2 (API): `rtk python -m compileall api`; `rtk rg -n "engines\.trtllm" api`;
`rtk rg -n "$S3_PAT" api pyproject.toml uv.lock`.

Task 3 (schemas/tools): `rtk python -m compileall tools`; `rtk rg -n "$S3_PAT" schemas tools`.

Task 4 (tests): `PYTHONPATH=api rtk python -c "import app.main"`;
`rtk python -m pytest -q -m "not gpu"`.

Task 5 (webui): structure + `rtk rg -n "$S3_PAT" webui`; artifact scan; best-effort lint/typecheck/vitest.

Task 6 (full): private-ref + weight/media + archive + cache + submodule scans; schema-sync diff.

`$S3_PAT` is defined in `docs/session_3/plan.md`.

## Failure Classification Rule

No source fix is allowed until the failing command is classified as BUG, SPEC_GAP,
AMBIGUITY, ENVIRONMENT, or TEST_BUG (recorded in
`docs/session_3/failure_arbiter.md`). The same failure twice triggers a new Failure
Arbiter entry before another fix attempt. Note the Session 2 precedent: private-repo
test taxonomies may drift; classify path/name drift as AMBIGUITY, not a code BUG.

## Review Axes (high risk -> sharded review)

- correctness
- security/safety
- tests
- architecture/maintainability
- performance

Reviewers are read-only and report severity, evidence (file/line), violated
contract clause, smallest safe fix, and confidence. Fix only High/Critical this
session; Medium needs 2+ reviewers or strong evidence; Nits optional.

## Adversarial Verifier Brief

Fresh-context verifier sees only: `docs/project_contract.md`,
`docs/session_3_contract.yaml`, `docs/session_3/**`, the `session-3` import diff,
and the recorded check outputs. It tries to falsify:

- the imported tree is curated and buildable (compileall + import + CPU tests);
- no private host/path/codename/secret/`.gitmodules`/submodule remains;
- `api/engines/trtllm/` and the legacy submodules are absent and unreferenced;
- the CPU test pass is not hollow (critical modules were actually imported);
- `schemas/openapi.json` is in sync with the app;
- changed files stay within the allowed blast radius (no `.github/`, `README.md`, `deploy/` edits, no weights/media);
- evidence/risk/handoff records suffice for MIG-S4 and MIG-S5.

## Done Condition

`GATE-MIG-S3-IMPORT` passes only when all are true:

- the curated, scrubbed source tree (`api/` minus trtllm, `webui/`, `schemas/`,
  `tools/`, CPU-safe `tests/`, `pyproject.toml`, `uv.lock`) is present;
- private-reference and weight/media/archive/cache/submodule scans return no
  release-blocking match;
- `compileall api`, torch-free `import app.main`, and `pytest -m "not gpu"` pass, or
  each failure is classified;
- `schemas/openapi.json` is in sync or the diff is dispositioned;
- `import_manifest.md` records INCLUDED/EXCLUDED/DEFERRED, and `scrub_report.md`
  records a clean final scan;
- sharded review and adversarial verification are PASS or have accepted
  classifications for any failure.
