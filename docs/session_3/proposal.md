# Session 3 Proposal - Curated WebUI/API Source Import and Scrub

Date: 2026-07-06
Session: MIG-S3
Status: Derived from approved brainstorming

## Motivation

The public repo has no runtime source, so CI (S5), Docker (S6), README (S7), and
release (S8) work cannot be verified. Session 3 imports the API and WebUI source
in curated form from the owner-provided private repo
`/data/home_feng/workspace/gitea/cosmos3-nano-webui`, while removing private
references, legacy submodule dependencies, bulky artifacts, and non-CPU-safe
material. A direct mirror is unsafe because the private tree contains private
hosts, private paths, 638 MB of legacy submodules, and 1265 files of private
development history.

## Agreed Changes

- Import via an explicit allowlist derived from the private repo's tracked files
  (Approach 1: manifest-driven copy + targeted scrub + CPU verification).
- Import `api/` except `api/engines/trtllm/`; keep the torch-free reasoning
  integration `api/engines/vllm/` and the decoupled HTTP client
  `api/engines/vllm_omni/`.
- Import the full Next.js `webui/` app (source, config, `package.json`,
  `pnpm-lock.yaml`, `public/urdf/`, unit tests).
- Import `schemas/openapi.json` (+ README) and `tools/checkpoint_prep/`.
- Import the CPU-safe test set only; exclude gpu-marked, `tests/equivalence/`,
  `tests/e2e/`, `tests/bench/`, `tests/deploy/`, and `test_trtllm_contract.py`.
- Import `pyproject.toml` and `uv.lock`.
- Drop `.gitmodules` and all `submodules/`; the WebUI repo consumes vLLM-Omni via
  the Session 2 public pin at the deploy layer (S6), not a submodule (INV-3).
- Keep `/data/models` as the documented public container-mount convention; drive
  real checkpoint locations through `COSMOS3_*_MODEL_DIR` env; scrub only the
  truly-private specifics (`10.147.19.203`, `/data/home_feng`, `/workspace/gitea`,
  `cosmos3-nano-quantization`, `-wfen`, `-dist`).
- Defer the entire `deploy/` tree to S6 and record it as a handoff item.
- Add source-level CPU smoke evidence and an OpenAPI schema-sync check.
- Commit imported source + refining docs at clean checkpoints on `session-3`; do
  not push.

## Capabilities

### New Capabilities

1. **Curated Source Import** (`curated_source_import`)
   - The public repo contains a curated, buildable `api/`, `webui/`, `schemas/`,
     `tools/`, and CPU-safe `tests/` tree plus `pyproject.toml`/`uv.lock`, imported
     from the private repo per an explicit include/exclude/defer manifest, with no
     public API route or request-shape change (INV-9).

2. **Private Reference Scrub** (`private_reference_scrub`)
   - Imported files contain no private host, private absolute path, private
     codename, secret, or private-repo reference. Real checkpoint locations are
     operator env inputs; `/data/models` remains only as a documented mount
     convention. A scrub report records the pattern, matches, dispositions, and
     final clean scan.

3. **Legacy Dependency Exclusion** (`legacy_dependency_exclusion`)
   - No legacy plain vLLM or TensorRT-LLM submodule, `.gitmodules`, or
     TensorRT-LLM engine code enters the public repo, and the kept API import
     graph loads without any excluded module.

4. **CPU Source Smoke** (`cpu_source_smoke`)
   - The imported source compiles, the FastAPI app imports torch-free, the CPU
     test set passes (or failures are classified), and the committed
     `schemas/openapi.json` matches what the app generates.

### Modified Capabilities

None. Session 3 introduces the first runtime source; it does not modify a
previously shipped WebUI-repo capability. Public API route names and request
shapes are preserved exactly as imported (INV-9); any deviation would be a
contract-gated change and is out of scope.

## Impact

Affected public repo areas (created by import):

- `api/**` (except `api/engines/trtllm/**`)
- `webui/**`
- `schemas/**`
- `tools/**`
- `tests/**` (CPU-safe subset)
- `pyproject.toml`, `uv.lock`

Affected public docs:

- `docs/session_3/**` (this refining pack + import manifest + scrub report + smoke
  evidence)
- `docs/evidence_map.md`, `docs/risk_register.md`
- `docs/eval_seed_cases.md` and `docs/eval_corpus/**` if an issue is caught/missed
- `docs/handoff.md` (Session End Protocol)

Explicitly not in scope:

- `deploy/**` (S6), `.github/**` (S5), `README.md` (S7), `submodules/**`,
  `.gitmodules`, model weights, generated media, private `docs/**`, the vLLM-Omni
  fork (S2, already pinned).

Dependency impact:

- `pyproject.toml` declares the server core (fastapi/uvicorn/pydantic/
  prometheus-client) and an opt-in `oracle` extra (torch/diffusers/etc.). No new
  production dependency is added by this session; the manifest is imported as-is
  and verified to reference only public sources.
