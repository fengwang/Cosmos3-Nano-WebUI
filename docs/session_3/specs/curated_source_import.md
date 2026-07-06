# Specification - Curated Source Import

Session: MIG-S3
Capability: Curated Source Import

## ADDED Requirements

### Requirement: API source is imported in curated form

The public repo SHALL contain the API runtime source under `api/`, imported from
the private repo's tracked `api/` files, EXCEPT `api/engines/trtllm/`. The imported
`api/` SHALL compile under CPython without CUDA or model weights.

#### Scenario: API tree is present and compiles

WHEN `python -m compileall api` is run from the repo root
THEN it SHALL exit 0
AND `api/app/main.py`, `api/app/routes/`, `api/jobs/`, `api/orchestrator/`,
`api/preprocessing/`, and `api/engines/{base,diffusers_oracle,diffusers_action,
vllm,vllm_omni}/` SHALL be present.

#### Scenario: The TensorRT-LLM engine is excluded

WHEN `api/engines/` is listed
THEN `api/engines/trtllm/` SHALL NOT be present
AND no kept file under `api/` SHALL import `engines.trtllm`.

### Requirement: WebUI source is imported in curated form

The public repo SHALL contain the Next.js WebUI under `webui/`, including source,
build config, `package.json`, and `pnpm-lock.yaml`, with no checked-in build
output, `node_modules`, or private host references.

#### Scenario: WebUI app and manifests are present

WHEN `webui/` is listed
THEN `webui/package.json`, `webui/pnpm-lock.yaml`, `webui/next.config.mjs`,
`webui/tsconfig.json`, `webui/app/`, `webui/components/`, `webui/lib/`, and
`webui/design-system/` SHALL be present
AND `webui/node_modules/`, `webui/.next/`, and any `dist/`|`build/` output SHALL be
absent.

### Requirement: Schemas and tools are imported

The public repo SHALL contain `schemas/openapi.json` and the
`tools/checkpoint_prep/` package.

#### Scenario: Schema and tools present

WHEN `schemas/` and `tools/` are listed
THEN `schemas/openapi.json` SHALL be present
AND `tools/checkpoint_prep/__init__.py` and its modules SHALL be present.

### Requirement: Only CPU-safe tests are imported

The public repo SHALL contain the CPU-safe test subset and MUST NOT contain
gpu-marked tests, `tests/equivalence/`, `tests/e2e/`, `tests/bench/`,
`tests/deploy/`, or `tests/test_trtllm_contract.py`.

#### Scenario: CPU tests present, GPU/equivalence/e2e absent

WHEN `tests/` is listed
THEN `tests/api/`, `tests/checkpoint_prep/`, and CPU-safe top-level `test_*.py`
SHALL be present
AND `tests/equivalence/`, `tests/e2e/`, `tests/bench/`, `tests/deploy/`, every
`*_gpu.py` file, and `tests/test_trtllm_contract.py` SHALL be absent.

#### Scenario: No kept test imports an excluded module

WHEN kept test files are scanned for imports of `engines.trtllm` or the
`equivalence` harness
THEN no kept test SHALL import an excluded module.

### Requirement: Public API routes and request shapes are preserved

Imported API route names and request/response shapes SHALL match the private
source exactly (INV-9). Session 3 SHALL NOT change public API behavior.

#### Scenario: OpenAPI route set is unchanged

WHEN the OpenAPI document generated from the imported app is compared to the
committed `schemas/openapi.json`
THEN the path set and operation methods SHALL be identical.

### Requirement: Import manifest records dispositions

Session 3 SHALL record an import manifest listing included, excluded, and deferred
paths with a reason for each.

#### Scenario: Manifest lists each area with a disposition

WHEN `docs/session_3/import_manifest.md` is read
THEN it SHALL list each top-level source area with an INCLUDED, EXCLUDED, or
DEFERRED disposition and a reason
AND it SHALL name `deploy/**` as DEFERRED to MIG-S6.
