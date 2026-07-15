# GPU-S1 Implementation Plan

Input: `docs/session_1/tasks.md`, `docs/session_1/design.md`,
`docs/session_1/specs/*.md`. Executed live against the real RTX 5090 in this
sandbox (owner-approved "Full live execution").

## Step 1 (Task 1) — sm_120 spike, before touching any file

Verification, not a regression test (no code exists yet to regress):

```bash
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv
docker pull vllm/vllm-openai:v0.24.0
docker run --rm --gpus all --entrypoint python3 vllm/vllm-openai:v0.24.0 -c "
import torch, vllm
print('torch', torch.__version__, 'cuda', torch.version.cuda)
print('vllm', vllm.__version__)
print('capability', torch.cuda.get_device_capability(0))
x = torch.randn(4096, 4096, device='cuda', dtype=torch.bfloat16)
y = x @ x
torch.cuda.synchronize()
print('matmul ok, sum=', y.sum().item())
"
```

**Gate:** if `capability` != `(12, 0)` or the matmul errors, STOP — this is
the contract's named human gate ("a build-failure class that needs a
base-image change"). Report findings and ask before choosing a replacement
tag. Do not silently substitute another tag.

No commit (no file changes yet).

## Step 2 (Task 2.1) — Rewrite `deploy/vllm-omni.Dockerfile`

Failing check already established (baseline): `docker compose -f
deploy/docker-compose.fp8.yml build vllm-omni` fails at the `pip install
--break-system-packages` step against the current file.

New file content (starting hypothesis — the exact `uv`/`pip` invocation may
need `--system` or a `--python` path once Step 1's image is inspected;
adjust in place if the first build attempt errors on that line specifically,
not by changing base image or fork pin):

```dockerfile
# syntax=docker/dockerfile:1
# vLLM-Omni generation-engine image (GPU-S1). Installs the pinned public fork from the
# immutable commit (INV-3) and serves an operator-mounted checkpoint on :8000
# (readiness: /v1/models). No weights are ever copied in (INV-2); the checkpoint
# is a runtime mount.

ARG BASE_IMAGE=vllm/vllm-openai:v0.24.0
FROM ${BASE_IMAGE}

# GPU-S1 immutable pin: commit SHA (a tag can be force-moved; the commit cannot).
ARG VLLM_OMNI_REF=697035018b70cef76b974a909d23371a9984c3f2
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Immutable commit — never a bare mutable branch (INV-3). Public HTTPS for reproducibility.
RUN if command -v uv >/dev/null 2>&1; then \
      uv pip install --no-cache-dir "git+https://github.com/fengwang/vllm-omni.git@${VLLM_OMNI_REF}"; \
    else \
      pip install --no-cache-dir "git+https://github.com/fengwang/vllm-omni.git@${VLLM_OMNI_REF}"; \
    fi

EXPOSE 8000
# Confirmed entrypoint (docs/model_setup.md §9). Guardrails stay ON by default;
# --no-guardrails is a runtime override (see docs/session_1/specs/vllm-omni-serve-entrypoint.md), not baked in here.
CMD ["vllm", "serve", "/models/checkpoint", "--omni", \
     "--host", "0.0.0.0", "--port", "8000", "--init-timeout", "1800"]
```

Apply with `Edit`/`Write` on `deploy/vllm-omni.Dockerfile`.

## Step 3 (Task 2.2-2.3) — Build and verify provenance

```bash
time docker compose -f deploy/docker-compose.fp8.yml build vllm-omni
docker history cosmos3-nano-vllm-omni:local --no-trunc | tail -n +1
docker inspect vllm/vllm-omni:cosmos3 --format '{{json .RootFS.Layers}}' > /tmp/cosmos3_layers.json
docker inspect cosmos3-nano-vllm-omni:local --format '{{json .RootFS.Layers}}' > /tmp/new_layers.json
comm -12 <(jq -r '.[]' /tmp/cosmos3_layers.json | sort) <(jq -r '.[]' /tmp/new_layers.json | sort)
```

**Check:** build exits 0; the `comm` intersection is empty (no shared layer
IDs with the forbidden prebuilt). Record base image tag + build duration.

**Self-critique (max 3 iterations if the build fails):** classify each
failure with the Failure Arbiter before changing anything — a missing apt
package is a BUG in this Dockerfile (fix here); a vllm-omni install error
that traces back to an actual upstream incompatibility with `v0.24.0` is the
named human gate (STOP, report, do not silently swap base images).

**Commit point:** `fix(gpu-s1): rebuild vllm-omni.Dockerfile from public vllm-openai base`
once the build is green.

## Step 4 (Task 3) — Serve + T2I, both checkpoints

```bash
docker compose -f deploy/docker-compose.fp8.yml up -d vllm-omni
curl -sf http://localhost:8000/v1/models
# T2I request against FP8 (exact request shape from docs/model_setup.md / api conventions)
curl -sf -X POST http://localhost:8000/v1/... -d '{...}' -o /tmp/gpu-s1-fp8-t2i.png
docker compose -f deploy/docker-compose.fp8.yml down
docker compose -f deploy/docker-compose.nvfp4.yml up -d vllm-omni
curl -sf http://localhost:8000/v1/models
curl -sf -X POST http://localhost:8000/v1/... -d '{...}' -o /tmp/gpu-s1-nvfp4-t2i.png
docker compose -f deploy/docker-compose.nvfp4.yml down
```

(Exact T2I request path/schema confirmed against the running server and the
fork's `recipes/cosmos3/Cosmos3-Nano.md` at execution time — the endpoint
shape is read-only knowledge, not something this session changes.)

**Check:** both requests return a valid image artifact; record hardware,
driver/CUDA, checkpoint revision, vLLM-Omni commit, request shape, and
artifact metadata (INV-8) into the evidence doc.

No commit yet (evidence capture happens in Step 6).

## Step 5 (Task 4) — Drop the local-image stopgap

```bash
rm deploy/docker-compose.local-image.yml
```

**Commit point:** `chore(gpu-s1): drop docker-compose.local-image.yml stopgap`
with a message citing PRD Owner Decision 8 and the removal reason from
`docs/session_1/specs/local-image-override-disposition.md`.

## Step 6 (Task 5) — Documentation sync

Edit `docs/release_checklist.md` §6 (flip the two `[ ]` build/entrypoint
items to `[x]` with the new evidence), `docs/evidence_map.md` (new rows:
build result, sm_120 confirmation for `v0.24.0`, FP8 T2I, NVFP4 T2I,
local-image disposition), `docs/risk_register.md` (R-01 → closed/advanced
with evidence; R-09 → closed, GPU host confirmed available).

**Commit point:** `docs(gpu-s1): record build/serve/T2I evidence + close R-01/R-09`

## Step 7 (Task 6) — Review and adversarial verification

Dispatch sharded review (5 axes) and a fresh-context adversarial verifier as
separate agents once Steps 2-6 are committed (see
`docs/session_1/execution_contract.md` for the brief). Fix High/Critical
findings only, re-run the specific check each finding affects, commit fixes
separately: `fix(gpu-s1): address sharded-review finding <id>`.

## Step 8 (Task 7) — Session close

Re-run the full deterministic check list from `session_1_contract.yaml`
end to end one more time on the final committed state, verify
`GATE-GPU-S1-DOCKERFILE`'s done condition, write `docs/handoff.md` and
`docs/eval_corpus/` seeds.

**Commit point:** `docs(gpu-s1): handoff + eval seeds`
