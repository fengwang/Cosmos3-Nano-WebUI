# Session 3 Brainstorming - Curated WebUI/API Source Import and Scrub

Date: 2026-07-06
Session: MIG-S3
Status: Approved design (owner approved on 2026-07-06)

## Context Explored

- Read `docs/prd.md`, `docs/project_contract.md`, `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/session_3.md`, `docs/session_3_contract.yaml`,
  the Session 1 manifests (`import_manifest.md`, `exclusion_manifest.md`,
  `scrub_checklist.md`, `inventory.md`), and the Session 2 `docs/handoff.md`.
- Confirmed the public repo is an empty seed: only `docs/`, `misc/logo.png`,
  `.gitignore`, and an empty `README.md` are tracked. `AGENTS.md`, `CLAUDE.md`,
  `ENVIRONMENTS.md`, `REVIEW.md`, `references/`, and `docs/agent_workflow/` are
  gitignored local scaffolding. No `api/`, `webui/`, `schemas/`, `tests/`,
  `tools/`, or `deploy/` exist yet.
- Confirmed Session 2 published the vLLM-Omni pin (tag
  `cosmos3-nano-webui-mig-s2` -> `697035018b70…`), consumed by later Docker work,
  not this session.
- Located the private source (owner-provided) at
  `the owner-provided private source repo`. It is a full repo with its
  own `session-1..session-8` development history and the target
  `api/ webui/ schemas/ tests/ tools/ deploy/ submodules/` layout. Tracked file
  counts: `docs` 1265, `webui` 158, `tests` 155, `api` 64, `deploy` 41,
  `tools` 7, `submodules` 3, `schemas` 2, plus root manifests.

## Key Findings That Shaped The Design

1. **The API is a FastAPI app with a torch-free import surface.** Heavy imports
   (`torch`, `vllm`, `tensorrt_llm`, `diffusers`) are deferred inside functions.
   `python -m compileall api` and `PYTHONPATH=api python -c "import app.main"` can
   run without CUDA or model weights.
2. **`api/engines/vllm/` is NOT vendored plain vLLM.** It is the reasoning plane's
   torch-free integration that builds `vllm serve` argv and shells out to an
   operator-provided binary (`COSMOS3_VLLM_BIN`). It is imported at module load by
   `app/main.py`, `app/routes/reasoning.py`, `app/errors.py`, and
   `orchestrator/planes.py|worker.py`, so it MUST be kept.
3. **`api/engines/vllm_omni/` is a decoupled HTTP client** (`http://vllm-omni:8000`
   via `urllib`); it does not import the `vllm_omni` package, so INV-3 is honored
   at the deploy layer (S6). Keep.
4. **`api/engines/trtllm/` is TensorRT-LLM conversion tooling** that is torch-free
   at import but not reachable from the API server (only its own test), and it
   hardcodes `submodules/TensorRT-LLM/...` paths.
5. **`submodules/` is huge and forbidden** (TensorRT-LLM 533 MB, vllm 105 MB) and
   `.gitmodules` points vllm-omni at private host `a private intranet host`.
6. **Concrete private tokens found in the candidate tree:** host `a private intranet host`,
   `a private home path`, `a private checkout root`, private repo `a sibling private quantization repo`,
   private checkpoint suffixes `-wfen`/`-dist`. No `hf_`/`sk-` secrets, no hidden
   large binaries outside `submodules/`.
7. **`/data/models` is used pervasively** as the checkpoint mount, including as the
   trust-boundary allowlist root in path-traversal tests. It is a generic container
   mount, not a home/secret.

## Clarifying Questions And Answers

| # | Question | Decision |
|---|---|---|
| Q0 | Where is the private source? | `the owner-provided private source repo` (owner-provided). |
| Q_A | How to treat `/data/models`? | **Keep as documented public container-mount convention**; drive real dirs via `COSMOS3_*_MODEL_DIR`; scrub only truly-private specifics. |
| Q_B | Which tests to import (CPU-scoped session)? | **CPU-safe only**: exclude gpu-marked, `tests/equivalence/`, `tests/e2e/`; defer GPU suites to S8. |
| Q_C | Keep or drop `api/engines/trtllm/`? | **Drop** the trtllm engine + its test; no proven public runtime need. |
| Q_D | Commit behavior? | **Commit locally at clean checkpoints on `session-3`, no push.** |

## Approaches Considered

### Approach 1 (chosen): Manifest-driven allowlist copy + targeted scrub + CPU verification
Build an explicit include-list from the private repo's tracked files, copy exactly
those files, apply a small enumerated set of scrub edits, then prove completeness
with import/compile/test/schema smoke checks.
- Pros: auditable diff; directly yields the required import manifest + scrub report;
  minimal transformation; completeness is verifiable (compile + import graph + tests).
- Cons: the allowlist must be maintained carefully; missing a needed file is caught
  by the import/compile/test smoke, not by copying blind.

### Approach 2 (rejected): Full-tree copy then prune + scrub
Copy the whole tree, then delete excluded classes and scrub.
- Rejected: broad import creates noisy diffs that hide private leaks (a named
  Session 3 failure mode), and weakens scrub auditability.

### Approach 3 (rejected): Rewrite curated source from scratch
- Rejected: throws away proven code; this is an import, not a rewrite; enormous and
  high-risk. The PRD says adapt old to new, not re-implement working runtime.

## Validated Design (Summary)

**Import scope**
- `api/`: app + engines except `engines/trtllm/` (kept: `base`, `diffusers_oracle`,
  `diffusers_action`, `vllm` [reasoning integration], `vllm_omni` [HTTP client]).
- `webui/`: full Next.js 15 / React 19 / pnpm app (source, `design-system/`,
  `components/`, `lib/` + `*.test.ts`, `public/urdf/` 16 KB, configs,
  `package.json`, `pnpm-lock.yaml`).
- `schemas/`: `openapi.json` + `README.md`.
- `tools/`: `checkpoint_prep/` (all 7).
- `tests/`: CPU-safe set — `tests/api/` (non-gpu), `tests/checkpoint_prep/`,
  top-level `test_*.py` (minus trtllm/gpu). Exclude `tests/equivalence/`,
  `tests/e2e/`, all `*_gpu.py`/gpu-marked, `tests/bench/`, `tests/deploy/`,
  `test_trtllm_contract.py`.
- root: `pyproject.toml`, `uv.lock`.

**Deferred to later sessions**
- Entire `deploy/**` -> S6 (Docker/Compose/overrides + GPU-diagnostic/bench tooling).
  `tests/bench/` and `tests/deploy/` are excluded to stay paired with that deferral.

**Excluded (forbidden or out-of-scope)**
- `submodules/**` and `.gitmodules` (forbidden, bulky, private host), `.github/**`
  (S5), private `docs/**` (private dev history), `README.md` (S7), caches/venvs/
  tmp/scratch.

**Scrub**
- Keep `/data/models` mount convention + `COSMOS3_*` env.
- Transforms: drop `.gitmodules`/`submodules/`; env-drive
  `tools/checkpoint_prep/copy_shared.py` `_BF16_BASE_REF` (default
  `/data/models/Cosmos3-Nano`); rephrase the `submodules/vllm/...` comment in
  `api/engines/vllm/reasoner_preflight.py`; verify the kept test set carries no
  `-wfen`/`-dist`/`a private git host`/private-venv strings.

**CPU smoke (no CUDA/weights)**
- `python -m compileall api`; `PYTHONPATH=api python -c "import app.main"`;
  `pytest -q -m "not gpu"` over imported tests; OpenAPI regen + diff vs
  `schemas/openapi.json`; scrub + weight/media/archive/cache/submodule/legacy scans.
- WebUI lint/typecheck/vitest are best-effort; if node/network is unavailable,
  classify ENVIRONMENT and hand to S5 (CI).

**Capabilities (spec files)**
- `curated_source_import` (includes WebUI), `private_reference_scrub`,
  `legacy_dependency_exclusion`, `cpu_source_smoke`.

**Persistence**
- Commit imported source + refining docs at clean checkpoints on `session-3`.
  Do not push.

## Owner-Approved Judgment Calls (not asked)
- Defer all of `deploy/` to S6.
- Exclude `tests/bench/` and `tests/deploy/` to stay consistent with the deploy
  deferral.
