# AM-S1 Design — Spike Probe Plan + Pre-Registered Decision Rubric

Date: 2026-07-24
Input: `docs/session_1/brainstorming.md`. Authority: `docs/session_1_contract.yaml`,
`docs/project_contract.md`, `docs/prd.md`. Evidence: `docs/evidence_map.md`.

## Context

AM-S1 is a **feasibility spike**, not a build. It answers four unknowns (S-A, S-C,
S-E, residency) with recorded evidence on the RTX 5090 against the **pinned FP8**
checkpoint, and emits an **owner-signed decision record**. The blast radius is
docs-only; the "implementation" is a sequence of read-only inspections and
throwaway/dev GPU wiring whose *output is evidence*.

The deploy topology (read from `deploy/docker-compose.{base,fp8}.yml`,
`api/engines/vllm_omni/endpoints.py`):

- `vllm-omni` service → container `cosmos3-nano-webui-vllm-omni`, serves internal
  `:8000`, **not host-published**; the `api` container starts/stops it via the
  mounted docker socket. Proven generation command:
  `vllm serve /models/checkpoint --omni --host 0.0.0.0 --port 8000 --init-timeout
  1800 --no-guardrails --vae-use-tiling --enable-layerwise-offload` (peak ~14.7 GiB
  on the 720p default).
- Because `:8000` (omni) is internal, the spike reaches it via a **standalone
  `docker run` of `cosmos3-nano-vllm-omni:local`** publishing `127.0.0.1:8000:8000`
  with the FP8 checkpoint mounted read-only and the *identical* command. This is
  the truest option-(a) test: one `vllm serve --omni` process, one resident model —
  if it answers both generation *and* `/v1/chat/completions`, (a) holds and
  plane-merge is trivially possible.

## Goals / Non-Goals

**Goals.** Confirm E-06 against the pinned checkpoint; determine per-mode `(a)`/`(c)`
for reasoning and action with recorded evidence against a pre-registered rubric;
decide the zero-BF16 action-packaging path; record VRAM footprints + the residency
implication; keep the CPU baseline green; obtain owner sign-off.

**Non-Goals.** Output **quality** (AM-S2/S3 owner gate); production wiring; NVFP4;
any persistent edit to `api/**`, `deploy/**`, `tools/checkpoint_prep/**`, weights,
or the WebUI. No re-exported checkpoint is produced or committed.

## Probe plan (ordered — cheap/no-GPU evidence first)

Each probe writes a raw artifact under `docs/session_1/evidence/` (commands +
outputs) and a one-line verdict against the rubric (§ Rubric).

### P0 — Baseline (done)
- `uv run pytest -m "not gpu"` → **523 passed** (green). Artifact: captured.
- `rg -n "action_" api/engines/diffusers_action/loader.py` → E-06 premise intact
  in code (graft reads `action_*` from base, raises `FileNotFoundError` if absent).

### P1 — E-06 confirmation vs the pinned FP8 checkpoint (no GPU)
Dependency-free safetensors header read (no torch): first 8 bytes = little-endian
uint64 header length `N`, next `N` bytes = JSON of tensor keys.
- Target A: `/data/models/Cosmos3-Nano-FP8-Blockwise/transformer/*.safetensors` →
  assert **zero** keys matching `^action_`.
- Target B: `/data/models/Cosmos3-Nano/transformer/*.safetensors` (BF16 base) →
  assert `action_*` keys **present** (`action_modality_embed`, `action_proj_in.*`,
  `action_proj_out.*`).
- **Verdict:** E-06 confirmed iff A has none and B has them.

### P2 — `checkpoint_prep` bundling evaluation (no GPU)
Read `tools/checkpoint_prep/{mutation,rewrite,safetensors_io,integrity_probe,
copy_shared,__main__}.py` + `tests/checkpoint_prep/**`. Answer: can the toolkit
express "**add** the `action_*` bf16 tensors into the quantized `transformer`
safetensors + reconcile any `action_gen`/config sidecar + integrity-probe the
result"? Examine the `-dist` prior-art: `Cosmos3-Nano-FP8-Blockwise-dist/`
(`reasoner/` subdir, `self_contained_provenance.json`, `*.s5-orig.bak`) — is it an
existing self-contained bundle, and does its provenance name the tool/steps used?
- **Verdict:** `bundle-via-checkpoint_prep (go)` | `alternative` + rationale.

### P3 — Reasoning option-(a) probe (GPU)
Start the standalone omni probe container (identical command). Then:
- `GET /v1/models` — what model id/arch is loaded.
- `GET /openapi.json` (and `/docs`) — enumerate the routes the **one** server
  exposes: is `/v1/chat/completions` present? any generation/omni routes? any
  action route (feeds P5)?
- If chat present: `POST /v1/chat/completions` with the pre-registered coherence
  prompts (below). Record status, `finish_reason`, and the raw completion text.
- **Coherence prompts** (feasibility bar, *not* quality):
  1. `"What is 2+2? Reply with just the number."` → expect contains `4`/`four`.
  2. `"In one sentence, what color is a clear daytime sky?"` → expect `blue`.
  3. `"List three primary colors, comma-separated."` → on-topic color list.
- **Coherence PASS** = HTTP 200, non-empty, `finish_reason` ∈ {stop,length} (not
  error), and ≥2/3 prompts on-topic & syntactically valid, off the quantized
  transformer with **no BF16 mounted**.

### P4 — Reasoning option-(c) fallback probe (GPU; only if P3 has no chat surface)
Two quick checks, thoroughness only:
- Restart the omni server as a *second* instance conceptually — but since it is the
  same fork, if P3 exposed no chat, note that the omni fork itself cannot serve
  chat (so a second omni instance is pointless).
- Optional: `vllm serve /models/checkpoint` **without** `--omni` → expect an
  arch-unrecognized error (the Cosmos3 omni arch needs the fork). Record the error.
- **Verdict:** if neither yields coherent chat off quantized weights, zero-BF16
  reasoning has **no** obvious path → reasoning `(c)` currently implies the BF16
  base vanilla reasoner → **explicit owner decision** (reshapes AM-S2).

### P5 — Action option-(a) surface probe (GPU)
From P3's `GET /openapi.json`: does the omni server expose any action-capable route
(`forward_dynamics`/`inverse_dynamics`/`policy`/action-typed completion)? Attempt a
minimal request against any candidate route.
- **Verdict:** `(a)` for action iff a real action route produces an action-shaped
  response. **Expected: none → `(a)` excluded for action.**

### P6 — Action option-(c) feasibility-load (GPU; no quality run)
Instantiate the `diffusers_action` engine on the 5090 via the repo loader
`api/engines/diffusers_action/loader.py:load_action_transformer(...)` with
`quant_dir=/data/models/Cosmos3-Nano-FP8-Blockwise`,
`base_action_dir=/data/models/Cosmos3-Nano/transformer`, in an image that carries
the diffusers fork + modelopt (candidate: `cosmos3-nano-vllm-omni:local`, else
`cosmos3-quant:latest`; identified at execution). Record whether the grafted
transformer **loads** (precision verify `GEN_TOWER_QUANTIZED = 505`) or **fails**.
- **Verdict:** `(c)-loads` (viable path for AM-S3, quality TBD there) | `(c)-blocked
  -by-D1` (critical — AM-S3 must fix loader/checkpoint compat first). **No**
  forward_dynamics/trajectory run.

### P7 — VRAM traces + residency implication (GPU)
`nvidia-smi --query-gpu=memory.used,memory.total --format=csv` sampled at: (i) idle;
(ii) omni server resident (generation model loaded); (iii) during a chat completion
(if P3 passed); (iv) diffusers_action loaded (P6, if it loads).
- **Verdict:** if reasoning `(a)` → confirm the single server serving both stays
  within 32 GiB (or is literally one model → no extra VRAM) → **plane-merge
  possible**. If `(c)` → note the reasoner is now ~quantized (not the ~26 GiB BF16
  in `coresidency.py` E-08) → **swap still required, but cheaper**; the E-08
  assumption is stale for AM-S2/S4.

## Pre-Registered Decision Rubric (frozen before probing)

| Mode / question | Evidence gate | Decision |
|---|---|---|
| **Reasoning** | P3 coherence PASS off quantized, zero-BF16 | **(a)** — omni serves reasoning; plane-merge candidate |
| | P3 chat present but degenerate/empty | (a) feasibility **doubtful** — record; reshapes AM-S2 (not a quality verdict) |
| | P3 no chat surface; P4 no zero-BF16 path | **(c) / blocked** — reasoning needs BF16 base ⇒ explicit owner decision |
| **Action** | P5 real action route responds | (a) — omni serves action (unexpected) |
| | P5 no action surface; P6 engine loads | **(c)-loads** — `diffusers_action` side-car plane viable for AM-S3 |
| | P5 no action surface; P6 load fails (D1) | **(c)-blocked-by-D1** — critical; AM-S3 must resolve first |
| **Zero-BF16 action packaging** | P1 gap confirmed + P2 toolkit can express the bundle | **bundle-via-checkpoint_prep (go)** |
| | P2 toolkit cannot express it | **alternative** (BF16 side-car as explicit owner decision, or custom export) + rationale |
| **Residency** | P7 single server both surfaces in budget | plane-merge possible (Studio+Reasoning share) |
| | P7 two residents | swap retained (evict-before-load), reasoner ~quantized ⇒ E-08 stale |

**Anti-conflation rule (frozen):** a "works" verdict for any mode requires the
evidence gate above; "the server loaded" or "the engine instantiated" alone is
recorded as *loaded*, never as *works*. Output **quality** is never judged here.

## Risks / Trade-offs

- **[Drift D1 blocks P6]** → not a spike failure; recorded as the action `(c)`
  verdict `(c)-blocked-by-D1` and handed to AM-S3.
- **[Omni image ENTRYPOINT vs CMD ambiguity]** → verify the Dockerfile
  ENTRYPOINT/CMD before `docker run`; pass the full `vllm serve …` argv (compose's
  `command:` starts with `vllm`, so entrypoint is not `vllm`).
- **[`:8000` host-port contention]** → run only the standalone omni probe (not the
  full stack) so nothing else binds host `:8000`.
- **[Cold model load ~minutes; init-timeout 1800 s]** → poll `GET /v1/models`
  until ready; cap wait; capture logs on timeout as a finding (failure mode #3).
- **[Wrong image for P6]** → try `cosmos3-nano-vllm-omni:local` first (has the
  diffusers fork), fall back to `cosmos3-quant:latest`; record which carried the
  deps.

## Migration / Rollback

No persistent change. Every probe container is `docker run --rm` (auto-removed) or
explicitly `docker rm`-ed; GPU returns to idle. Weights are read-only mounts. If any
probe wedges the GPU, `docker rm -f` the probe container and re-check `nvidia-smi`.
The full stack is left as found (down).

## Open Questions (resolved at execution)

- Which image carries diffusers-fork + modelopt for P6 (recorded in evidence).
- Whether `-dist` is an already-working self-contained bundle (P2) — if so, it is
  strong prior-art for the packaging `go` decision (but is **not** the pinned
  public checkpoint and is not committed/relied-on as a shipped artifact).
