# AM-S4 Micro-Plan (TDD)

Executable, test-first. Exact paths + snippets + commands + commit points. References
`specs/**` (what) and `design.md` (how/why).

Conventions: run the smallest relevant check after each step; commit only at a clean
checkpoint (owner-authorized commits). All paths repo-root-relative.

---

## Task 1 — Deterministic wiring tests (red first)

**1.1 `tests/deploy/test_fp8_allmodes_wiring.py`** — pure-file YAML parse (no docker/GPU).

```python
# Load base + fp8 compose as YAML; assert all-modes + zero-BF16.
import pathlib, yaml
DEPLOY = pathlib.Path(__file__).resolve().parents[2] / "deploy"

def _load(name):
    return yaml.safe_load((DEPLOY / name).read_text())

def test_fp8_has_omni_and_reasoner_services():
    base, fp8 = _load("docker-compose.base.yml"), _load("docker-compose.fp8.yml")
    services = set(base.get("services", {})) | set(fp8.get("services", {}))
    assert {"vllm-omni", "vllm-reasoner"} <= services

def test_fp8_mounts_only_quantized_no_bf16_base():
    fp8 = _load("docker-compose.fp8.yml")
    vols = [v for svc in fp8["services"].values() for v in (svc.get("volumes") or [])]
    text = "\n".join(vols)
    assert "/models/base" not in text
    assert "Cosmos3-Nano:" not in text and "/Cosmos3-Nano/" not in text  # BF16 base source
    assert "FP8" in text  # the quantized checkpoint dir
```

**1.2 `tests/deploy/test_no_legacy_overlay.py`**

```python
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]

def test_reasoning_overlay_deleted():
    assert not (ROOT / "deploy/docker-compose.reasoning.yml").exists()

def test_with_reasoning_stripped():
    assert "WITH_REASONING" not in (ROOT / "deploy/api.Dockerfile").read_text()

def test_up_fp8_reasoning_retired():
    assert "up-fp8-reasoning" not in (ROOT / "Makefile").read_text()

def test_bf16_env_removed():
    env = (ROOT / ".env.example").read_text()
    for var in ("COSMOS3_BASE_DIR", "COSMOS3_REASONER_MODEL_DIR", "COSMOS3_VLLM_BIN"):
        assert var not in env
```

**1.3 `tests/deploy/test_reasoner_util_matches_contract.py`**

```python
import pathlib, yaml
ROOT = pathlib.Path(__file__).resolve().parents[2]

def _reasoner_util():
    fp8 = yaml.safe_load((ROOT / "deploy/docker-compose.fp8.yml").read_text())
    cmd = fp8["services"]["vllm-reasoner"]["command"]
    i = cmd.index("--gpu-memory-utilization")
    return float(cmd[i + 1])

def test_reasoner_gpu_util_equals_contract():
    import sys; sys.path.insert(0, str(ROOT / "api"))
    from engines.vllm.coresidency import CoResidencyContract
    assert _reasoner_util() == CoResidencyContract().gpu_memory_utilization
```

**1.4** Run red baseline:
```
uv run pytest tests/deploy -q   # 1.1 fails on BF16 assertion? no — currently passes wiring;
                                # 1.2 FAILS (overlay/WITH_REASONING/up-fp8-reasoning/env still present)
```
Expected red: 1.2 fails (legacy still present). 1.1/1.3 may already pass (wiring exists) —
that is fine; they guard against regression. Record which are red and why.

_Checkpoint C1: commit `test(am-s4): deterministic zero-BF16 all-modes wiring tests (red)`._

---

## Task 2 — Deploy unification (green)

**2.1 `Makefile`** — cold-start + retire the reasoning posture. Remove `REASON`, drop
`up-fp8-reasoning` from `.PHONY`/help. New targets:
```makefile
up-fp8:
> $(COMPOSE) $(FP8) up -d --no-start
> $(COMPOSE) $(FP8) stop vllm-omni vllm-reasoner
> $(COMPOSE) $(FP8) start api webui
up-nvfp4:
> $(COMPOSE) $(NVFP4) up -d --no-start
> $(COMPOSE) $(NVFP4) stop vllm-omni
> $(COMPOSE) $(NVFP4) start api webui
```
(nvfp4 stops only `vllm-omni` — it has no reasoner service.)

**2.2** `git rm deploy/docker-compose.reasoning.yml`.

**2.3 `deploy/api.Dockerfile`** — remove `ARG WITH_REASONING`, the `base-1` CUDA stage,
and the if/else; single lean stage:
```dockerfile
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 UV_NO_CACHE=1
COPY --from=docker:28-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=ghcr.io/astral-sh/uv:0.11.25 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY api/ ./api/
ENV PYTHONPATH=/app/api
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Update the header comment to drop the reasoning-build description.

**2.4 `.env.example`** — delete `COSMOS3_BASE_DIR`, `COSMOS3_REASONER_MODEL_DIR`,
`COSMOS3_VLLM_BIN`, the "LEGACY BF16 subprocess overlay" section, and the
`huggingface-cli download nvidia/Cosmos3-Nano` block. Keep the zero-BF16 all-modes
wiring + FP8/NVFP4 download lines. Add a one-line note that no BF16 base is needed.

**2.5** `base.yml`/`fp8.yml` — comment only: note the orchestrator cold-starts/owns the
heavy planes (no wiring change).

Run: `uv run pytest tests/deploy -q` → **green**. Then
`docker compose -f deploy/docker-compose.fp8.yml config >/dev/null && echo ok` and the
nvfp4 render.

_Checkpoint C2: commit `feat(am-s4): cold-start make up-fp8 + delete legacy BF16 surface`._

---

## Task 3 — Coresidency R-08 (comment)

**3.1 `api/engines/vllm/coresidency.py`** — rewrite the `DEFAULT_GPU_MEMORY_UTILIZATION`
comment: the ~26 GiB resident is the **FP8 reasoner** (quantized weights + KV cache) at
0.85 util, not ~16 GiB BF16 base weights; the container-stop eviction frees it; keep
`0.85`. Do not touch the constant or `CoResidencyContract`.

Run: `uv run pytest tests/test_coresidency_unit.py tests/deploy -q` → green.

_Checkpoint folded into C3._

---

## Task 4 — Docs reconciliation

**4.1 `docs/model_setup.md`**:
- §1 checkpoint table: BF16 base row → "legacy/dormant paths only — not required for any
  default mode".
- §4 env table: `COSMOS3_REASONER_MODEL_DIR`/`COSMOS3_BASE_ACTION_DIR` → legacy/dormant,
  no default for a live mode.
- §5 mount layout: drop the base dir from the default (note it optional/legacy).
- §6 matrix: reasoning row → "FP8 reasoner container off the quantized checkpoint;
  **GPU-verified FP8 (AM-S2, owner PASS)**"; confirm action row (AM-S3) intact.
- §8 operator setup: keep step 3's "no BF16 base" (already AM-S2/S3), align §5/§1.

Run: `uv run pytest -m "not gpu" -q` (full) → green.

_Checkpoint C3: commit `docs(am-s4): reconcile model_setup + coresidency footprint to zero-BF16`._

---

## Task 5 — Full host verification

```
uv run pytest -m "not gpu"                                  # green
docker compose -f deploy/docker-compose.fp8.yml config      # all-modes, no BF16 mount
docker compose -f deploy/docker-compose.nvfp4.yml config    # renders
rg -n "up-fp8-reasoning|WITH_REASONING|COSMOS3_BASE_DIR" Makefile deploy .env.example
git diff --exit-code schemas/openapi.json                   # clean (INV-8)
```
Classify any failure via the Failure Arbiter before fixing.

---

## Task 6 — Review + adversarial verification

Sharded review (6 axes) → `sharded_review.md`; fix High/Critical only + re-check.
Fresh-context adversarial verifier → `adversarial_verification.md`. Then re-run Task 5.

---

## Task 7 — GPU all-modes smoke (agent-driven)

1. Confirm `.env` resolves the FP8 mount to the fresh checkpoint
   (`docker compose … config` → check `source:`; R-11 stale-pin guard).
2. `make down && make build && make up-fp8`; `docker ps` → only api+webui running.
3. Studio `t2i` (baseline PNG) → Action agibotworld policy/FD + av ID → `/v1/reason`
   (observe evict/load swap logs) → Studio `t2i` again (swap back, INV-2). Capture peak
   VRAM per step (`nvidia-smi`), assert never co-resident, ≤32 GiB.
4. Record `GPU-AM-ALLMODES-FP8` + `GPU-AM-T2I-NOREGRESS` to `docs/session_4/evidence/`.
5. Owner final all-modes/quality confirmation → `GATE-AM-S4-ORCHESTRATION`.

---

## Task 8 — Close-out

Update `docs/evidence_map.md` (AM-S4 audit block), `docs/risk_register.md`
(R-07 resolved, R-08 reconciled, R-14 held), `docs/eval_seed_cases.md`,
`docs/handoff.md`. Verify the done condition; state AM-S5 warnings.

_Checkpoint C4: commit `docs(am-s4): close session — evidence/risk/eval/handoff + GPU smoke`._
