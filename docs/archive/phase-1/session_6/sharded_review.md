# Session 6 Sharded Review - Local-Build Docker and Compose

Session: MIG-S6 · Risk: high · Gate: `GATE-MIG-S6-DOCKER`
Axes: correctness · security · tests · architecture · performance
(`docs/agent_workflow/prompts/sharded_review.md`). Five independent read-only reviewers;
findings deduplicated below, most severe first, each with disposition. Per protocol,
Critical/High are fixed and re-checked; Lows fixed opportunistically when cheap and
tied to a contract adversarial case; out-of-blast-radius items are deferred with a record.

## Findings and disposition

### C-1 (Critical, tests) — the failure-arbiter doc re-tripped the committed scanner
`docs/session_6/failure_arbiter.md` quoted the raw `mnt_path` literal five times; because
the scanner's `SCAN_ROOTS` include `docs/`, the doc itself became five fresh findings and
turned the committed private-reference scan **red** after FA-1 had made it green.
**Fixed:** neutralized the literal to `/mnt/‹dir›` (non-matchable) and recorded it as
FA-2. Re-check: `uv run python tests/test_private_ref_scan.py` → **clean (0 findings)**.

### H-1 (High, correctness) — a repo-root operator `.env` was silently ignored
Compose's project directory is `deploy/` (the first `-f`), so it auto-loads `deploy/.env`,
not the repo-root `.env` that `.env.example` tells operators to create; the `Makefile`
passed no `--env-file`. Result: `COSMOS3_API_KEY`, ports, and mount overrides were dropped
(API silently up with **auth disabled**). Violates spec `external_checkpoint_mounts`
("operator can override the mount") and INV-4. **Fixed:** the `Makefile` now auto-passes a
repo-root `.env` via `--env-file` when present (`ENV_FILE := $(wildcard .env)`), a no-op
when absent so `make config-*` still renders on defaults; `.env.example` documents the
placement + the direct-`docker compose` alternatives. Re-check: a temp repo-root `.env`
(`WEBUI_PORT=31337`, `COSMOS3_API_KEY=testkey123`) is now honored in the render.

### H-2 (High, architecture) — `WITH_REASONING=1` installed no vLLM
The reasoning build ran `uv sync --extra oracle`, but the `oracle` extra (and `uv.lock`)
contain **no `vllm`**, while the reasoner needs `from vllm import LLM` / `vllm serve`
(`api/engines/vllm/loader.py`, `api/orchestrator/planes.py`). The image would build yet be
unable to reason — the "build succeeds, required dep missing" trap. Violates spec
`local_build_images` ("install the vLLM reasoning stack"). **Fixed:** the `WITH_REASONING`
branch now also `uv pip install vllm==0.23.0` (the pin the code references; a build-time
install since it is not in `uv.lock`); Dockerfile/spec/design text corrected to state torch
+ vLLM are installed and torch/vLLM/CUDA compatibility is validated at `MIG-S8`. (The lean
default is unaffected — verified torch-free.)

### S-1 (Low–Medium, security) — docker-socket privilege claimed tracked but had no risk row
Design D-6 said the `/var/run/docker.sock` mount is "recorded as a risk," and the proposal
called it "R-06-adjacent," but no risk row existed and `container.py` cites a stale `R-15`
(the original project's numbering). **Fixed:** added **R-16** (docker-socket root-equivalent
privilege — confined controller, loopback ports, socket-proxy deferred) to
`docs/risk_register.md`; corrected the proposal to reference R-16.

### S-2 (Low, security) — vLLM-Omni pinned by a mutable tag, not the immutable commit
`vllm-omni.Dockerfile` defaulted `VLLM_OMNI_REF` to the tag `cosmos3-nano-webui-mig-s2`; a
tag can be force-moved (the contract's "pin is mutable" adversarial case). **Fixed:**
defaulted to the immutable commit `697035018b70cef76b974a909d23371a9984c3f2` (tag kept in a
comment).

### S-3 (Low, security) — default published ports on all interfaces with auth off
`0.0.0.0` publish + empty `COSMOS3_API_KEY` (auth disabled) + the docker-socket mount is a
risky default on a shared host. **Fixed:** published ports now bind `${BIND_ADDR:-127.0.0.1}`
(loopback) by default with a documented `0.0.0.0` override; `.env.example` notes the
key/exposure interaction. Verified: default renders `host_ip: 127.0.0.1`; override renders
`0.0.0.0`.

### S-4/A-4/P-1 (Low, security+arch+perf) — `uv:latest` / untagged `docker:cli` unpinned
Inconsistent with the design's own pin discipline (all `FROM` bases are tag-pinned).
**Fixed:** pinned `ghcr.io/astral-sh/uv:0.11.25` and `docker:28-cli` (both confirmed to
exist); digest-pinning remains an S8 hardening.

### P-2 (Low, performance) — uv wheel cache baked into the api layer
Negligible for the lean default, multi-GB for the reasoning build. **Fixed:** `ENV
UV_NO_CACHE=1` in the runtime stage.

### A-2 (Low, arch/correctness) — `COSMOS3_BASE_ACTION_DIR` inert in the reasoning overlay
Read only by the dormant `diffusers_action` engine (`COSMOS3_GEN_ENGINE=diffusers`), not the
reasoner. **Fixed:** added a comment stating it serves the action/diffusers path and shares
the same BF16 base mount (kept, since action/`forward_dynamics` needs that mount).

### A-3 (Low, arch) — `.env.example` "defaults also baked in code" overstated for path vars
The code's own fallbacks are `/data/models/*`, not the `/models/*` in-container targets.
**Fixed:** re-scoped the annotation to the wiring vars and noted the mount targets are
compose-set (code fallback differs).

### T-1 (High, tests) — no durable regression gate for the `deploy/` surface — DEFERRED
The render + weight-copy checks live only in the `Makefile` (manual); the committed scanner's
`SCAN_ROOTS` exclude `deploy/`/`.env.example`/`Makefile`, and a CI render job would touch
`.github/**`. Both the scanner (`tests/**`) and CI (`.github/**`) are **out of the S6 blast
radius**. **Deferred** to `MIG-S7`/`MIG-S8` (or a contract amendment): recorded in the
handoff, risk register, and an eval seed. S6 mitigation: the `make scan` target bundles the
weight-copy + private-reference scans for manual/local use.

### X-1 (pre-existing, security/correctness) — WebUI sends `Authorization: Bearer`, API checks `X-API-Key` — DEFERRED
If an operator sets `COSMOS3_API_KEY`, the WebUI→API proxy path would 401 (`webui/lib/proxy.ts`
vs `api/app/auth.py`). Both files are **out of the S6 blast radius** (product code). **Deferred:**
documented as a gotcha in `.env.example` (near `COSMOS3_API_KEY`), the handoff, and an eval seed
for a later session; not fixable in S6.

## Notes (tracked, no S6 change)
- **vLLM-Omni serve entrypoint** in `vllm-omni.Dockerfile` (`CMD … vllm_omni.entrypoints…`)
  is an unverified best-effort, overridable via Compose `command:`; confirmed at `MIG-S8`.
- **Single-GPU `count: all`** on both `api` (reasoning overlay) and `vllm-omni` is the
  compose-visible face of the orchestrator-serialized reasoning⊕generation model; real
  co-residency is an `MIG-S8` runtime concern.
- The spec's 3-`-f` reasoning render (`-f base -f fp8 -f reasoning`) duplicates the
  vllm-omni GPU reservation in the output (valid; cosmetic). The Makefile path
  (`-f fp8 -f reasoning`) does not. No action.

## Verified-correct (skeptical checks that passed)
api CMD/paths (`.venv/bin/uvicorn app.main:app`, `PYTHONPATH=/app/api`); omitting `schemas/`
is correct (OpenAPI built from the app at runtime); full service wiring matches the baked-in
code (`http://api:8000`, `http://vllm-omni:8000`, `cosmos3-nano-webui-vllm-omni`); fp8/nvfp4 +
overlay renders exit 0 with correct labels and no unset-var warnings; `include:` base resolves;
webui standalone runner is self-contained; `.dockerignore` yields a ~2.3 MB context; layer
caching order correct; apt lists cleaned; no `COPY . .`; no submodule; weight-copy + private-ref
scans clean.

## Outcome
No unresolved Critical/High. C-1, H-1, H-2 fixed and re-checked; S-1..S-4, A-2, A-3, P-1, P-2
fixed. T-1 and X-1 are out-of-blast-radius and deferred with records (risk register + handoff +
eval seeds). Re-run of the deterministic checks after fixes: all green (see
`docs/session_6/adversarial_verification.md` for the independent reproduction).
