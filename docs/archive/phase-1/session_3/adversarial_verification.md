# Session 3 Adversarial Verification

Date: 2026-07-06
Session: MIG-S3
Verifier: fresh-context, read-only; saw only project + session contracts, the
`git diff 388a334..HEAD`, and the session evidence docs (treated as claims to
falsify). Did not see the implementation conversation. Re-ran all deterministic
checks with its own commands (torch-free Python 3.12 venv; node 26 / pnpm 11.3.0).

## Verdict: PASS (GATE-MIG-S3-IMPORT)

No disproven claims. The completion claim held under independent re-execution.

## Independently Reproduced

- **Blast radius:** all 314 changed paths within `blast_radius.allowed_files`; zero
  in `forbidden_files` (`.github/**`, `README.md`, `submodules/**`, `.gitmodules`).
- **CPU smoke (the deterministic gate):** `compileall api` = 0; `compileall tools`
  = 0; torch-free `import app.main` = 0 (FastAPI app builds); `pytest -m "not gpu"`
  = **467 passed, 3 skipped (numpy-absent), 0 failed**.
- **Hollow-test falsification:** inverting the readiness gate in `api/app/health.py`
  in an isolated copy produced **2 real test failures** — the suite exercises
  product behavior, not just imports. All core product modules import from the real
  `api/` tree; no kept file imports `trtllm`/`equivalence`/`TensorRT`; excluded
  trees/files are absent.
- **INV-1 (source):** clean of private homes, RFC1918 hosts, private git host,
  sibling-repo name, `-wfen`, `Blockwise-dist`, `hf_`/`sk-`/PRIVATE KEY,
  `submodules/...|TensorRT-LLM`.
- **INV-1 (`docs/session_3/**`, the adversarial focus):** no real private values;
  remaining occurrences are scrub-pattern fragments / disposition tables (policy
  language explicitly permitted by the MIG-S2 eval seed) and the public destination
  path. FA-6/R1 fix genuinely applied.
- **INV-2:** no weights/media/archives/caches tracked; only binary is
  `misc/logo.png` (out of S3 scope); no binary hidden under an odd extension;
  `agibotworld.urdf` is 11 KB UTF-8 XML.
- **INV-3 / INV-10:** `api/engines/vllm_omni/` is a stdlib-`urllib` HTTP client, not
  a vendored/submoduled fork; `uv.lock` sources are all public (self, pinned public
  `diffusers` git commit, `download.pytorch.org`, `pypi.org`).
- **INV-9 / schema sync:** regenerated OpenAPI is byte-for-byte identical to the
  committed `schemas/openapi.json`; `tests/test_openapi.py` passes.
- **Sharded-review fixes landed:** R2 (`schemas/README.md` direct export cmd), R3
  (`base.py` clean of trtllm/tensorrt), R4 (`test_openapi.py` message).

## Unsupported (not disproven)

- WebUI toolchain (`pnpm typecheck/test/lint`) is best-effort (D8), not part of the
  deterministic gate; the verifier confirmed supporting facts (39 `*.test.ts(x)`
  files tracked, manifest+lockfile present, no `node_modules`/`.next` tracked) but
  did not re-run a live `pnpm install`. (The implementer's run: install OK,
  typecheck OK after generated `next-env.d.ts`, vitest 208 passed, lint clean.)

## Strongest Counterexample Found

A broad `-dist`/`10.x` scan hit 9 source files — all confirmed false positives
(generic "distribution" checkpoint terminology, the `requires-dist` packaging key,
and the `nvidia-curand-cu12` PyPI version `10.3.9.90`). The genuinely-private
tokens are absent from source. Does not rise to a violation.

## Clarification Recorded

`docs/evidence_map.md` lines 22–23 cite public HF pages
`huggingface.co/wfen/Cosmos3-Nano-{FP8,NVFP4}-Blockwise` — here `wfen` is the
**public HF org namespace**, distinct from the scrubbed private `-wfen` checkpoint
suffix. Pre-existing public-URL citation, not a leak.
