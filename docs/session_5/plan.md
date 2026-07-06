# Session 5 Plan - CPU-Only CI and Test Stabilization

Session: MIG-S5
Derived from: `tasks.md` (checklist) + `design.md` (how) + `specs/*.md` (what)

TDD note: several deliverables are configuration (workflow YAML, dependency group)
where the "failing test" is the deterministic check itself. For the scrub scanner —
real logic — tests precede implementation in the same module.

## Task 1 — Baseline fixes and CPU test group

1.1 `tests/api/test_gen_ipc.py:232` — remove the stray `f`:
```python
# before:  assert '"2400"' in source, f"Expected default '2400' in work() source; INV-P3-4 violated"
# after:   assert '"2400"' in source, "Expected default '2400' in work() source; INV-P3-4 violated"
```

1.2 `tests/api/test_oracle_adapter_audio.py:46` — annotate the intentional import:
```python
from engines.base import EngineInfo, GenerationRequest, Precision  # noqa: E402 (stubs injected above must precede this import)
```

1.3 `pyproject.toml` — add the group after `[dependency-groups]`:
```toml
[dependency-groups]
dev = ["pytest>=8.0", "httpx>=0.27", "openapi-spec-validator>=0.7", "ruff>=0.6"]
# Torch-free CPU test deps: let the image/video artifact-encoder tests run in CI
# instead of skipping for a missing numpy. Pins mirror the `oracle` extra.
test-cpu = ["numpy>=1.26", "pillow>=10.0", "imageio>=2.34", "imageio-ffmpeg>=0.5", "safetensors>=0.4"]
```
Then: `uv lock` (regenerates `uv.lock`).

1.4 Verify (checks):
```bash
uv run ruff check api tests            # exit 0
uv sync --frozen --group test-cpu
uv run pytest -m "not gpu" -rs -q      # encoder tests run (no numpy skip); all pass
uv run python -c "import importlib.util,sys; sys.exit(importlib.util.find_spec('torch') is not None)"  # torch absent -> exit 0
```
Commit point: `feat(s5): ruff-clean tests + torch-free test-cpu group`.

## Task 2 — GPU test isolation

2.1 `tests/conftest.py` (new):
```python
"""Root test fixtures/policy for the CPU loop.

GPU isolation: tests marked ``@pytest.mark.gpu`` require the RTX 5090 and are
skipped on the torch-free CPU loop unless ``COSMOS3_ENABLE_GPU_TESTS`` is truthy.
CI additionally passes ``-m "not gpu"`` (belt-and-suspenders). Convention: a
GPU-only test module MUST guard heavy imports (e.g. ``pytest.importorskip("torch")``)
so pytest can import it during collection on a CPU runner without the ``oracle`` extra.
"""
import os
import pytest

_GPU_OPT_IN = "COSMOS3_ENABLE_GPU_TESTS"


def _gpu_enabled() -> bool:
    return os.environ.get(_GPU_OPT_IN, "").strip().lower() in {"1", "true", "yes", "on"}


def pytest_collection_modifyitems(config, items):
    if _gpu_enabled():
        return
    skip_gpu = pytest.mark.skip(reason=f"gpu test skipped on CPU loop; set {_GPU_OPT_IN}=1 to run")
    for item in items:
        if "gpu" in item.keywords:
            item.add_marker(skip_gpu)
```

2.2 Verify with a throwaway module, then delete it:
```bash
printf 'import pytest\n@pytest.mark.gpu\ndef test_probe():\n    assert False\n' > tests/test__gpu_probe_tmp.py
uv run pytest tests/test__gpu_probe_tmp.py -rs -q                     # 1 skipped
COSMOS3_ENABLE_GPU_TESTS=1 uv run pytest tests/test__gpu_probe_tmp.py -q  # 1 failed (ran)
rm tests/test__gpu_probe_tmp.py
```
Commit point: `feat(s5): conftest gpu-marker skip guard (COSMOS3_ENABLE_GPU_TESTS)`.

## Task 3 — Private reference scan

3.1 `tests/test_private_ref_scan.py` (new) — structure (ACD):
- Data: `WEIGHT_MEDIA_EXTS`, `SECRET_PATTERNS` (private-key header, `hf_[A-Za-z0-9]{20,}`,
  `sk-[A-Za-z0-9]{20,}`), `PRIVATE_PATH_PATTERNS` (`/home/<user>`, other real roots),
  `ALLOWED_PLACEHOLDERS`, `SCAN_ROOTS`, `EXCLUDE_PATHS` (scanner file, scrub checklist,
  `.git`, `.venv`, `node_modules`, lockfiles, binaries).
- Calculation: `scan_text(rel_path, text) -> list[Finding]` and
  `scan_tree(root) -> list[Finding]` (pure; walk provided by caller or a thin reader).
- Actions (edges): file reading, and the pytest assertion / CLI exit.
- Tests in the same module (write first, expect failure until functions exist):
```python
# NOTE: fixtures are built by concatenation so no literal secret-shaped string
# exists in a committed doc/scanner file (EV-MIG-SCRUB-COMMAND-SANITY).
def test_secret_header_is_caught():
    assert scan_text("x", "-----BEGIN " + "OPENSSH PRIVATE KEY-----")

def test_hf_and_sk_tokens_caught():
    assert scan_text("x", "token=hf_" + "A" * 32)
    assert scan_text("x", "key=sk-" + "A" * 32)

def test_weight_extension_caught():
    assert find_weight_media("models/unet.safetensors")

def test_placeholder_not_flagged():
    assert not scan_text("docs/x.md", "/path/to/Cosmos3-Nano-FP8-Blockwise")

def test_clean_tree_has_no_findings():
    findings = scan_tree(REPO_ROOT)
    assert findings == [], "\n".join(map(str, findings))
```
3.2 Iterate patterns until `test_clean_tree_has_no_findings` passes; tune
`EXCLUDE_PATHS`/`ALLOWED_PLACEHOLDERS` for any false positive found on the current
tree. Run:
```bash
uv run pytest tests/test_private_ref_scan.py -q      # all pass, clean tree
uv run python tests/test_private_ref_scan.py         # __main__ CLI, exit 0
```
Commit point: `feat(s5): committed private-reference/secret scan (test + CLI)`.

## Task 4 — CI workflow

4.1 WebUI baseline (informs the workflow):
```bash
cd webui
pnpm install --frozen-lockfile
pnpm gen:api && git diff --exit-code lib/api/schema.d.ts   # schema types in sync
pnpm typecheck || echo "TYPECHECK-NEEDS-BUILD"             # empirical: does it need build?
pnpm build
pnpm lint && pnpm typecheck && pnpm test
```
Record the typecheck-needs-build result in evidence; keep `build` regardless.

4.2 `.github/workflows/ci.yml` (new) — skeleton:
```yaml
name: ci
on: [push, pull_request]
permissions:
  contents: read
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<pin>
      - uses: astral-sh/setup-uv@<pin>
        with: { enable-cache: true }
      - run: uv python install 3.12
      - run: uv sync --frozen --group test-cpu
      - run: uv run ruff check api tests
      - run: uv run pytest -m "not gpu"
  webui:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: webui } }
    env: { NEXT_TELEMETRY_DISABLED: "1" }
    steps:
      - uses: actions/checkout@<pin>
      - uses: pnpm/action-setup@<pin>
        with: { version: 11.3.0 }
      - uses: actions/setup-node@<pin>
        with: { node-version: 22, cache: pnpm, cache-dependency-path: webui/pnpm-lock.yaml }
      - run: pnpm install --frozen-lockfile
      - run: pnpm gen:api && git diff --exit-code lib/api/schema.d.ts
      - run: pnpm build
      - run: pnpm lint
      - run: pnpm typecheck
      - run: pnpm test
```
Action versions pinned to current major tags at implementation time.

4.3 Validate:
```bash
uv run python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml ok')"
# optional: actionlint .github/workflows/ci.yml
```
Commit point: `feat(s5): CPU-only ci.yml (python + webui jobs)`.

## Task 5 — Developer command list

5.1 `docs/session_5/local_checks.md` — the exact `uv`/`pnpm` commands per CI step,
the manual GPU command (`COSMOS3_ENABLE_GPU_TESTS=1 pytest -m gpu`), and the scrub
CLI. Commit with the docs.

## Task 6 — Verification and review

6.1 Full deterministic checks (Python + WebUI + scrub); classify any failure via
`docs/agent_workflow/prompts/failure_arbiter.md` → `docs/session_5/failure_arbiter.md`.
6.2 Sharded review per `docs/agent_workflow/prompts/sharded_review.md` (5 axes) →
`docs/session_5/sharded_review.md`; fix only High/Critical; re-check.
6.3 Adversarial verification per `docs/agent_workflow/prompts/adversarial_verifier.md`
→ `docs/session_5/adversarial_verification.md`.

## Task 7 — Close

7.1 Amend `docs/session_5_contract.yaml` `allowed_files` (D10).
7.2 Update `docs/evidence_map.md`, `docs/risk_register.md` (R-05/R-10/R-14),
`docs/eval_seed_cases.md`; add `docs/eval_corpus/mig_s5_*.md`.
7.3 Verify `GATE-MIG-S5-CI`; write `docs/handoff.md`; state residual risks.
Commit point: `docs(s5): review, adversarial verification, evidence/risk, handoff`.
