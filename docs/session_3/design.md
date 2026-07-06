# Session 3 Design - Curated WebUI/API Source Import and Scrub

Date: 2026-07-06
Session: MIG-S3
Risk: high

## Context

The public repo is an empty seed. The private source at
`the owner-provided private source repo` contains the full product:
a FastAPI backend (`api/`), a Next.js WebUI (`webui/`), an OpenAPI schema
(`schemas/`), CPU + GPU tests (`tests/`), checkpoint tooling (`tools/`), Docker /
diagnostic deploy support (`deploy/`), three legacy git submodules
(`submodules/{vllm,TensorRT-LLM,vllm-omni}`), and 1265 files of private
development history under its own `docs/`.

Constraints come from `docs/project_contract.md` (INV-1..INV-10),
`docs/session_3_contract.yaml` (blast radius, invariants, adversarial cases), and
the Session 1 manifests. The vLLM-Omni dependency is already pinned publicly by
Session 2 and is consumed at the deploy layer (S6), not here.

Stakeholders: the owner (release authority) and later sessions S4 (HF
checkpoints), S5 (CPU CI), S6 (Docker), S7 (README), S8 (release gate).

## Goals

- A curated, buildable public source tree (`api/`, `webui/`, `schemas/`, `tools/`,
  CPU-safe `tests/`, `pyproject.toml`, `uv.lock`) imported without private leaks,
  legacy submodules, weights, media, or bulky evidence.
- A concrete import manifest (included / excluded / deferred) and a scrub report.
- Deterministic CPU smoke evidence proving the tree compiles, imports, tests
  green (or classified), and its OpenAPI schema is in sync.
- Preserved public API route names and request shapes (INV-9).

## Non-Goals

- No vLLM-Omni fork edits (S2). No HF checkpoint validation (S4). No GitHub Actions
  finalization (S5). No Docker runtime validation (S6). No README rewrite (S7).
- No import of `deploy/**`, `.github/**`, `submodules/**`, `.gitmodules`, private
  `docs/**`, model weights, or generated media.
- No public API behavior change; no new production dependency.

## Decisions

### D1: Manifest-driven allowlist copy (not full-tree prune, not rewrite)
Copy exactly the allowlisted files, then scrub. **Why:** an explicit allowlist
yields an auditable diff and the required manifest, and avoids the "broad import
hides private leaks" failure mode. Alternatives: full-tree-then-prune (noisy,
risky) and rewrite-from-scratch (discards proven code) — both rejected.

### D2: Keep `api/engines/vllm/` and `api/engines/vllm_omni/`; drop `api/engines/trtllm/`
`engines/vllm/` is the torch-free reasoning integration (builds `vllm serve` argv,
shells out to `COSMOS3_VLLM_BIN`) and is imported at module load across the app,
so it is required. `engines/vllm_omni/` is a decoupled `urllib` HTTP client to the
omni container (INV-3 satisfied at S6). `engines/trtllm/` is TensorRT-LLM
conversion tooling, torch-free at import but unreachable from the server and
bound to `submodules/TensorRT-LLM`; it has no proven public runtime need.
**Why:** honors "exclude legacy unless a runtime dependency is proven" and the
clean-design mandate (remove deprecated paths). Alternative (keep trtllm scrubbed)
rejected — it re-introduces the "legacy TensorRT reachable" adversarial case for
no beta benefit.

### D3: Drop `.gitmodules` and `submodules/` entirely
The WebUI repo consumes vLLM-Omni through the Session 2 public pin at the deploy
layer; plain vLLM and TensorRT-LLM are out of milestone 1. `.gitmodules` also
carries private host `a private intranet host`. **Why:** INV-3, the forbidden-files list,
and the 638 MB size. Alternative (scrub `.gitmodules` to public URLs) rejected —
milestone 1 has no submodules by contract.

### D4: `/data/models` is a documented public mount convention, not a private path
It is a generic container mount and the trust-boundary allowlist root in path
tests. Keeping it avoids churning ~30+ test assertions and preserves the
path-traversal semantics under test. Real checkpoint directories are operator env
inputs (`COSMOS3_*_MODEL_DIR`). **Why:** owner decision Q_A; the exclusion
manifest allows env/placeholder handling and `/data/models` is neither a home dir
nor a secret. Alternative (replace everywhere) rejected — high churn, higher risk
of altering tested behavior.

### D5: Import only the CPU-safe test set
Exclude gpu-marked tests, `tests/equivalence/`, `tests/e2e/`, `tests/bench/`,
`tests/deploy/`, and `test_trtllm_contract.py`. **Why:** S3's test scope is
"CPU-only unit/lint/typecheck/stub tests that do not require CUDA or model
weights", the GPU suites carry the most private paths, and full-surface GPU
validation is an S8 manual gate (FR-9). Alternative (import GPU tests scrubbed)
rejected for this session — they cannot run in CPU CI and multiply scrub risk.

### D6: Defer all of `deploy/` to S6
`deploy/` is Dockerfiles + Compose + overrides + GPU-diagnostic/bench tooling; the
Session 1 manifest assigns Docker/Compose to S6, and no piece is cleanly
non-Docker or CPU-relevant enough to justify importing now. **Why:** keeps S3
focused and avoids importing config S6 will own and rewrite. Recorded as an
explicit handoff/known-gap.

### D7: Add an OpenAPI schema-sync smoke check
`schemas/openapi.json` is generated by `api/app/openapi_export.py` and consumed by
the WebUI `gen:api` script. Regenerate and diff on import. **Why:** the named
failure mode "generated API types are stale after import"; gives a deterministic
guard now and a ready CI check for S5.

### D8: WebUI checks are best-effort, Python checks are required
Python smoke (compileall, app import, pytest -m "not gpu", schema-sync) is
required and deterministic. WebUI lint/typecheck/vitest require node + network
for `pnpm install`; if unavailable they are classified ENVIRONMENT and handed to
S5. **Why:** S3's deterministic checks are Python-centric; CI (S5) owns the JS
toolchain gate. Structure + no-private-ref + manifest/lockfile presence remain
required for the WebUI.

## Risks / Trade-offs

- **[Import misses a needed module, tests pass hollow]** -> `compileall api` +
  `import app.main` + `pytest -m "not gpu"` prove the kept import graph resolves;
  the allowlist is derived from `git ls-files`, not hand-typed per file.
- **[Excluding legacy breaks public imports]** -> `api/engines/__init__.py` is
  import-light (verified); no kept module imports `engines.trtllm` (verified); a
  kept-test grep for excluded-module imports runs before smoke.
- **[A private default path remains]** -> enumerated scrub token set + a full
  recursive scan over the imported tree; scrub report must show a clean final scan.
- **[Large binary hidden under odd extension]** -> extension + path-fragment
  artifact scans over the imported set; largest-file check during import.
- **[Stale generated schema]** -> D7 schema-sync check.
- **[`/data/models` judged a private path by a reviewer]** -> documented decision
  D4 with owner sign-off recorded here and in the scrub report.
- **[Noisy diff hides a leak]** -> allowlist copy (D1) + per-area commits keep the
  diff reviewable.

## Migration Plan

1. Establish baseline (empty-repo scans; record expected pre-import failures).
2. Generate the include/exclude/defer allowlist from the private repo's tracked
   files; write `import_manifest.md`.
3. Import + scrub in dependency order: root manifests -> `api/` -> `schemas/` ->
   `tools/` -> CPU-safe `tests/` -> `webui/`. Apply scrub edits as each area lands.
4. Run per-area targeted checks; classify any failure before fixing.
5. Run full CPU smoke + all scans; write `scrub_report.md` + smoke evidence.
6. Sharded review (5 axes); fix High/Critical; re-check.
7. Adversarial verification against `GATE-MIG-S3-IMPORT`.
8. Update evidence/risk, write handoff + eval seeds.

Rollback: all work is local commits on `session-3` (no push); a bad import area is
reverted by dropping its checkpoint commit. No external state changes.

## Open Questions

- None blocking. If S5 later needs a scrubbed `.env`/env-contract reference that
  currently lives under `deploy/`, it can import one from the private repo under
  the S5/S6 contract; this session records the env contract in the handoff instead.
