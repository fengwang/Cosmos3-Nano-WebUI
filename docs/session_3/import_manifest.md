# Session 3 Import Manifest - Included / Excluded / Deferred

Date: 2026-07-06
Session: MIG-S3
Source: `/data/home_feng/workspace/gitea/cosmos3-nano-webui` (owner-provided private repo)
Method: allowlist copy from the private repo's `git ls-files`, then targeted scrub.

## Summary

296 source files imported into the public repo:

| Area | Included | Notes |
|---|---:|---|
| `api/` | 59 | full app + engines EXCEPT `api/engines/trtllm/` |
| `webui/` | 158 | full Next.js 15 app incl. `webui/.gitignore` |
| `tests/` | 68 | CPU-safe subset |
| `tools/` | 7 | `checkpoint_prep/` |
| `schemas/` | 2 | `openapi.json`, `README.md` |
| root | 2 | `pyproject.toml`, `uv.lock` |
| **Total** | **296** | |

## INCLUDED (with reason)

- **`api/**` (59)** — API runtime needed for public beta routes + CPU tests. Kept
  engines: `base`, `diffusers_oracle`, `diffusers_action`, `vllm` (torch-free
  reasoning integration, imported at module load), `vllm_omni` (decoupled HTTP
  client). Compiles + imports torch-free.
- **`webui/**` (158)** — Next.js UI source, `design-system/`, `components/`,
  `lib/` (+ `*.test.ts`), `public/urdf/` (16 KB), configs, `package.json`,
  `pnpm-lock.yaml`. No build output.
- **`tests/**` (68)** — `tests/api/` (non-gpu), `tests/checkpoint_prep/`, top-level
  `test_*.py` (CPU, non-gpu). Run from public inputs.
- **`tools/checkpoint_prep/**` (7)** — CPU checkpoint tooling, compiles clean.
- **`schemas/openapi.json` + `README.md`** — OpenAPI contract consumed by the app
  test and the WebUI `gen:api` script.
- **`pyproject.toml`, `uv.lock`** — server core (torch-free) + opt-in `oracle`
  extra; references only public sources; resolves offline from cache.

## EXCLUDED (with reason)

- **`api/engines/trtllm/` (5)** — TensorRT-LLM conversion tooling; not reached by
  the server; bound to the excluded TensorRT-LLM submodule; no proven public
  runtime need (Q_C).
- **`tests/equivalence/` (52)**, **`tests/e2e/` (20)** — GPU/weights-oriented and
  private-path-heavy; out of CPU scope; deferred to S8 manual gates (Q_B).
- **`tests/bench/` (7)**, **`tests/deploy/` (1)** — exercise `deploy/`, which is
  deferred to S6.
- **all `*_gpu.py` / gpu-marked (11)** — require the RTX 5090 + weights (Q_B).
- **`tests/test_trtllm_contract.py` (1)** — tests the excluded trtllm engine.
- **`tests/test_action_metrics.py`, `tests/test_reasoning_metrics.py` (2)** —
  import `equivalence.metrics.*` (under the excluded `tests/equivalence/`); belong
  to the equivalence suite (see `failure_arbiter.md`).
- **`tests/api/test_s7_evidence_lib.py` (1)** — dynamically loads
  `docs/session_7/outputs/evidence_lib.py` (excluded private docs); see
  `failure_arbiter.md`.
- **`submodules/` (3 gitlinks + ~638 MB)** and **`.gitmodules`** — forbidden;
  `.gitmodules` also carries private host `10.147.19.203`. vLLM-Omni is consumed
  via the Session 2 public pin at the S6 deploy layer (INV-3).
- **`.github/**`** — CI is S5. **`README.md`** — S7. **private `docs/**` (1265)** —
  private development history/evidence.
- **caches / venvs / `tmp/` / `.scratch/`** — rebuildable local state.

## DEFERRED to MIG-S6

- **`deploy/**` (41)** — Dockerfiles, `docker-compose.*.yml`, `overrides/*.yml`,
  `.dockerignore`, `bench/`, `diag/`, `Makefile`, `.env.example`. Docker/Compose is
  S6 scope (Session 1 manifest). No piece is cleanly non-Docker or CPU-relevant
  enough to import now. S5/S6 may import a scrubbed env-contract reference under
  their contracts.

## Verification

See `docs/session_3/source_smoke.md` (CPU smoke) and `docs/session_3/scrub_report.md`
(scrub + final scans). All contract deterministic scans return clean; the imported
tree compiles, imports torch-free, and its CPU test suite passes.
