# Session 3 Plan - Curated WebUI/API Source Import and Scrub

Session: MIG-S3
Inputs: `docs/session_3/tasks.md`, `docs/session_3/design.md`, `docs/session_3/specs/*`

Conventions:

```bash
SRC=/data/home_feng/workspace/gitea/cosmos3-nano-webui
DST=/workspace/github.repo/Cosmos3-Nano-WebUI
# Session 3 private-reference pattern (fallback; $PRIVATE_REF_PATTERN unset):
S3_PAT='10\.147\.[0-9.]+|/data/home_feng|/workspace/gitea|(^|[^a-z])gitea|cosmos3-nano-quantization|-wfen|-dist|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|BEGIN [A-Z ]*PRIVATE KEY'
```

Copy uses `git ls-files` so only tracked files move (caches/venvs/node_modules are
never listed). TDD here means: identify the deterministic check derived from a spec
scenario that fails before the step (e.g. `compileall api` fails: no `api/`), then
import/scrub the smallest set to make it pass.

## Task 1 - Baseline And Allowlist

1. Baseline (expected: scans clean/empty, compileall fails - no `api/`):
   ```bash
   cd "$DST"
   rtk rg --files | rg -n "$S3_PAT" || echo "clean"
   rtk python -m compileall api ; echo "exit=$?  (expected non-zero: no api/ yet)"
   ```
2. Generate allowlists (record counts):
   ```bash
   git -C "$SRC" ls-files 'api/**' | grep -v '^api/engines/trtllm/' > /tmp/inc_api.txt
   git -C "$SRC" ls-files 'schemas/**' 'tools/**' > /tmp/inc_schema_tools.txt
   git -C "$SRC" ls-files 'tests/**' \
     | grep -vE '^tests/(equivalence|e2e|bench|deploy)/' \
     | grep -vE '_gpu\.py$' \
     | grep -vE '^tests/test_trtllm_contract\.py$' > /tmp/inc_tests.txt
   git -C "$SRC" ls-files 'webui/**' > /tmp/inc_webui.txt
   ```
3. Write `docs/session_3/import_manifest.md` (INCLUDED/EXCLUDED/DEFERRED + reasons).
- Commit: `docs(s3): baseline + curated import manifest`.

## Task 2 - Import API And Scrub

1. Failing check first: `rtk python -m compileall api` (fails, no `api/`).
2. Copy allowlisted API files:
   ```bash
   cd "$DST"
   while read f; do mkdir -p "$(dirname "$f")"; cp "$SRC/$f" "$f"; done < /tmp/inc_api.txt
   ```
3. Copy root manifests: `cp "$SRC/pyproject.toml" "$SRC/uv.lock" "$DST/"`.
4. Scrub: edit `api/engines/vllm/reasoner_preflight.py` - replace the
   `submodules/vllm/.../models/cosmos3.py` comment with a public reference to the
   pinned vLLM-Omni fork's Cosmos3 reasoner mapper (no `submodules/` path).
5. Verify:
   ```bash
   rtk python -m compileall api && echo OK
   rtk rg -n "engines\.trtllm" api ; echo "expect no matches"
   rtk rg -n "$S3_PAT" api pyproject.toml uv.lock ; echo "expect clean"
   ```
- Commit: `feat(s3): import curated api source (trtllm/submodules excluded, scrubbed)`.

## Task 3 - Import Schemas And Tools

1. Copy: `while read f; do mkdir -p "$(dirname "$f")"; cp "$SRC/$f" "$f"; done < /tmp/inc_schema_tools.txt`.
2. Scrub `tools/checkpoint_prep/copy_shared.py`: make `_BF16_BASE_REF` read
   `os.environ.get("COSMOS3_BF16_BASE_DIR", "/data/models/Cosmos3-Nano")`.
3. Verify: `rtk python -m compileall tools && rtk rg -n "$S3_PAT" schemas tools ; echo clean`.
- Commit: `feat(s3): import schemas + checkpoint_prep tools (scrubbed)`.

## Task 4 - Import CPU-Safe Tests

1. Copy: `while read f; do mkdir -p "$(dirname "$f")"; cp "$SRC/$f" "$f"; done < /tmp/inc_tests.txt`.
2. Straggler check - any kept gpu-marked test or excluded-module import:
   ```bash
   rtk rg -ln "pytest\.mark\.gpu" tests            # if any remain, ensure -m 'not gpu' skips or exclude
   rtk rg -ln "engines\.trtllm|from equivalence|import equivalence" tests
   ```
   Confirm `test_action_metrics.py` / `test_reasoning_metrics.py` reference trtllm
   only as engine-label strings (no import); otherwise classify and fix.
3. Verify (needs server deps fastapi/uvicorn/pydantic/prometheus-client + pytest/httpx):
   ```bash
   PYTHONPATH=api rtk python -c "import app.main" && echo IMPORT_OK
   rtk python -m pytest -q -m "not gpu"
   ```
   Classify any failure via the Failure Arbiter before fixing.
- Commit: `test(s3): import CPU-safe test suite`.

## Task 5 - Import WebUI

1. Copy: `while read f; do mkdir -p "$(dirname "$f")"; cp "$SRC/$f" "$f"; done < /tmp/inc_webui.txt`.
2. Verify structure + scrub + no build output:
   ```bash
   test -f webui/package.json && test -f webui/pnpm-lock.yaml && echo STRUCT_OK
   rtk rg --files webui | rg -n "(^|/)(node_modules|\.next|dist|build)(/|$)" ; echo "expect none"
   rtk rg -n "$S3_PAT" webui ; echo "expect clean"
   ```
3. Best-effort toolchain (S8/D8): if `node`+network available,
   `cd webui && pnpm install --frozen-lockfile && pnpm lint && pnpm typecheck && pnpm test`;
   else classify ENVIRONMENT and hand to S5.
- Commit: `feat(s3): import Next.js webui source`.

## Task 6 - Full Checks And Scrub Report

1. Full scans over the imported tree:
   ```bash
   cd "$DST"
   rtk rg -n "$S3_PAT" api webui schemas tests tools pyproject.toml uv.lock
   rtk sh -lc 'rg --files | rg -n "\.(safetensors|pt|pth|ckpt|mp4|mov|avi)$"'
   rtk sh -lc 'rg --files | rg -n "\.(zip|tar|tar\.gz|tgz|7z|rar)$"'
   rtk sh -lc 'rg --files | rg -n "(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|node_modules|dist|build|\.next|coverage)(/|$)"'
   rtk sh -lc 'rg --files | rg -n "(^|/)submodules/(vllm|TensorRT-LLM|vllm-omni)(/|$)|(^|/)TensorRT-LLM(/|$)"'
   test ! -e .gitmodules && echo "no .gitmodules OK"
   ```
2. Schema-sync:
   ```bash
   PYTHONPATH=api rtk python -c "import json,app.openapi_export as e; import app.main as m; \
     doc=e.build_openapi(m.app) if hasattr(e,'build_openapi') else m.app.openapi(); \
     open('/tmp/gen_openapi.json','w').write(json.dumps(doc,indent=2,sort_keys=True))"
   rtk sh -lc 'diff <(jq -S . schemas/openapi.json) <(jq -S . /tmp/gen_openapi.json) && echo SCHEMA_IN_SYNC'
   ```
   (Adjust to the actual exporter API discovered in `api/app/openapi_export.py`.)
3. Write `docs/session_3/scrub_report.md` + smoke evidence.
- Commit: `docs(s3): scrub report + CPU smoke evidence`.

## Task 7 - Review, Verification, Handoff

1. Sharded review (5 axes) -> `docs/session_3/sharded_review.md`; fix only High/Critical; re-run affected checks.
2. Adversarial verifier -> `docs/session_3/adversarial_verification.md`; classify any failure.
3. Update `docs/evidence_map.md`, `docs/risk_register.md`; write `docs/handoff.md`; add
   `docs/eval_corpus/mig_s3_*.md` seeds + update `docs/eval_seed_cases.md`.
- Commit: `docs(s3): sharded review, adversarial verification, handoff, eval seeds`.

## Failure Handling

Classify every failing check (BUG / SPEC_GAP / AMBIGUITY / ENVIRONMENT / TEST_BUG)
before any fix; record in `docs/session_3/failure_arbiter.md`. If the same failure
repeats twice, open a Failure Arbiter entry before another attempt.
