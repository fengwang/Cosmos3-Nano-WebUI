# AM-S2 Brainstorming — Zero-BF16 FP8 Reasoning via the vLLM Fork

Date: 2026-07-25 · Session: AM-S2 · Risk: high
Inputs: `docs/prd.md`, `docs/project_contract.md`, `docs/evidence_map.md`,
`docs/risk_register.md`, `docs/session_2.md`, `docs/session_2_contract.yaml`,
`docs/handoff.md`, `docs/session_1/` (AM-S1 decision record + P3 evidence).
Authority: this file records the collaborative design exploration and the
owner-approved validated design. It supersedes the *framing* in `session_2.md`
(which predates the AM-S1 findings) where they conflict; the invariants in
`project_contract.md` still bind, as amended in §6.

## 1. Context & reframe (what changed vs the written contract)

`session_2.md` was authored at blueprint time and frames AM-S2 as "wire the
mechanism AM-S1 selected (option a omni-chat, or option c side-car)". The AM-S1
execution audit and this session's byte-level probes refute that framing:

- **Omni chat is image-bound.** `vllm serve --omni` `/v1/chat/completions`
  returns a PNG, not text (`docs/session_1/evidence/P3-reasoning-omni-chat.md`).
  Option (a) as written is dead for reasoning.
- **The deployed quantized checkpoint cannot be served by *stock* vLLM as a
  reasoner.** Byte-confirmed (2026-07-25): the repo's own fail-closed guard
  `python3 api/engines/vllm/reasoner_preflight.py /data/models/Cosmos3-Nano-FP8-Blockwise`
  → `REJECT quant_sidecar_present: layers.0.mlp.down_proj.weight_quantizer._amax`.
  The understanding-tower FFNs (`layers.*.mlp.*`) are blockwise-FP8; stock vLLM
  can't dequant them (`api/engines/vllm/reasoner_preflight.py:8-11`).
- **A bundled BF16 reasoner exists but is *rejected* by the owner.** The `-dist`
  checkpoints ship a self-contained BF16 `reasoner/` understanding tower
  (`/data/models/Cosmos3-Nano-FP8-Blockwise-dist/reasoner`, passes the preflight,
  ~29 GB, `copy_shared (P6-S6)` from the BF16 base). It would satisfy
  "no separate base download" — but the owner has ruled **BF16 out entirely**
  (§2), so this is *not* the target.
- **The owner's vLLM fork already has the text path.** `fengwang/vllm@33c4f35`
  registers `Cosmos3ForConditionalGeneration` as a **text** multimodal model
  (`vllm/model_executor/models/registry.py:361`), with a `WeightsMapper` that
  keeps the understanding tower (`layers.*`→`language_model.model.*`, `lm_head`)
  and drops the generation tower + audio/action embeds
  (`vllm/model_executor/models/cosmos3.py`), a fully wired
  `compute_logits()`→`lm_head` path, and blockwise-FP8 kernels already in the
  standard linear forward. So `vllm serve <quantized>` **without `--omni`**
  *should* decode text off the FP8 understanding tower — zero BF16, and quite
  possibly with **no fork change** (a serving-config change, not new kernels).

Net: the session is **not** "accept the documented BF16 side-car". It is "prove a
*genuinely* zero-BF16 FP8 reasoning path off the quantized checkpoint, forking
vLLM only as far as needed", then wire it and GPU-verify.

## 2. Owner decisions this session (2026-07-25 interview)

1. **Zero-BF16 is absolute** for reasoning — no separate BF16 base, no bundled
   BF16 `reasoner/`. The written contract's "documented BF16 exception" (INV-4
   escape) is **removed**.
2. **Fork vLLM if needed**, using the local fork `the local vLLM fork (fengwang/vllm)`
   (`git@github.com:fengwang/vllm.git`, HEAD `33c4f35`).
3. **Prove FP8 end-to-end this session**; NVFP4 stays AM-S5 (FP8-first).
4. **Reasoner runs as its own container** built from the fork (not an api
   subprocess) → the api image drops torch+vLLM+`WITH_REASONING`.
5. **No BF16 fallback ever** — if zero-BF16 can't be reached, **stop and report**.

## 3. Approaches considered

| # | Approach | Verdict | Rationale |
|---|---|---|---|
| A | Reasoner = **own container from the fork**, `vllm serve <quantized>` no `--omni`, separate residency plane (swap) | **CHOSEN** (owner) | Only path that fully drops BF16 + `WITH_REASONING` from the api image; reuses the proven `ContainerPlaneWorker` pattern; keeps the evict-before-load safety net (INV-5); isolates the reasoner from the omni `t2i` path (protects INV-2). |
| B | Keep reasoner as an **api subprocess**, re-pointed at the quantized checkpoint + fork vLLM | Rejected | Keeps torch+vLLM+`WITH_REASONING` in the api image → only a *transitional* INV-4 win; AM-S4 would still have to containerize. |
| C | **Merge into the omni container** (Studio+Reasoning share one resident model) | Deferred | Best VRAM (plane-merge), but needs an omni-package text-modality flag; AM-S1 showed omni chat is hard-bound to image output. Revisit in AM-S3/S4 if the VRAM save is wanted. |

## 4. Validated design

### 4.1 Spike-first, with a pre-registered decision rubric

The whole design is gated on one unproven GPU behavior; resolve it **before** any
wiring, on a throwaway container (no repo/checkpoint edits, read-only mounts).

**Probe.** `docker run` the fork image; `vllm serve /models/checkpoint`
**no `--omni`**, FP8 checkpoint mounted read-only, **no BF16 mount**; poll
`/v1/models`; then `POST /v1/chat/completions` with the AM-S1 coherence prompts.

**Pre-registered rubric (frozen before probing):**

| Gate | Evidence | Verdict |
|---|---|---|
| Loads | arch recognized; blockwise-FP8 `modelopt` weights load without error, no BF16 mount | necessary, not sufficient |
| Emits **text** | `/v1/chat/completions` returns a token stream, `finish_reason ∈ {stop,length}`, content is **text not an `image_url`** | necessary |
| Coherent | ≥2/3 pre-registered prompts on-topic & syntactically valid | **feasibility PASS** |
| Any of the above fails | e.g. image output, load error, arch unrecognized | **feasibility FAIL** → classify |

- Coherence prompts (feasibility bar, *not* quality): `"What is 2+2? Reply with
  just the number."` (→ 4/four), `"In one sentence, what color is a clear
  daytime sky?"` (→ blue), `"List three primary colors, comma-separated."`.
- **Anti-conflation (eval seed `EV-AM-CHAT-IS-IMAGE`):** "server loaded" / HTTP
  200 alone is recorded as *loaded*, never *works*. Output **quality** is the
  owner's manual gate, never judged here.
- **On FAIL:** classify with the Failure Arbiter. If a *small* fork change
  unblocks it (e.g. register a text-only `Cosmos3ForCausalLM` alias, or fix the
  modelopt load path), make it in `fengwang/vllm`, re-probe. If it *balloons*,
  **stop and report** (record feasibility findings + a scoped follow-up). Never
  fall back to BF16.

### 4.2 Target serving architecture (once the spike passes)

- New **`vllm-reasoner` container** built from `fengwang/vllm` at a pinned commit;
  command `vllm serve <quantized> --served-model-name cosmos3-reasoner` (no
  `--omni`); internal port (e.g. `:8001`); readiness `/v1/models`.
- Orchestrator gains a **second `ContainerPlaneWorker`** for `Plane.REASONING`
  (mirrors the omni one). **Swap / evict-before-load retained** (INV-5) — reasoner
  and generation never co-reside.
- `VllmReasonerStream` re-pointed from the `:8765` subprocess to the reasoner
  container's `/v1/chat/completions` (now **text**). **API shape unchanged**
  (INV-8); WebUI `/chat`→`/v1/reason` untouched.
- **api image drops** torch + vLLM + the `WITH_REASONING` build split; the
  BF16-base subprocess wiring (`reasoning_spec`/`server_launch_argv`/
  `SubprocessPlaneWorker` for reasoning) is **retired for this stack**.

### 4.3 Component changes (what/where)

- `api/engines/vllm/reasoner_preflight.py` → accept a **fork-servable quantized**
  source (blockwise-FP8), replacing the BF16-only gate (or retarget it to the new
  container path).
- `api/engines/vllm/loader.py` `ReasonerConfig` → default dir = quantized
  checkpoint, `dtype=auto`, container launch (not in-process subprocess).
- `api/orchestrator/planes.py` + `api/app/main.py` → reasoning branch builds a
  reasoner **container** worker.
- `api/engines/vllm_omni/` container controller → generalized, or a sibling
  reasoner controller added.
- `deploy/docker-compose.base.yml`/`fp8.yml` → add `vllm-reasoner`;
  `deploy/api.Dockerfile` → drop `WITH_REASONING`; `.env.example` → reasoner
  points at the quantized checkpoint + fork image, BF16 defaults removed; new
  `deploy/vllm-reasoner.Dockerfile` (fork pin).
- **CPU tests** (~11) pinning the BF16-subprocess wiring → **updated** to the
  container-served quantized wiring (never reverted): `tests/test_reasoner_adapter_unit.py`,
  `tests/api/test_orchestrator_stub.py`, `tests/api/test_reasoner_preflight_unit.py`,
  `tests/test_coresidency_unit.py`, `tests/test_integ_swap_*`, `tests/api/test_routes_reasoning.py`.

### 4.4 Test / verification strategy

- New CPU tests: reasoner spec builds a **container** worker at the quantized dir
  with `dtype=auto`; preflight **accepts** a blockwise-FP8 source and still
  rejects a genuinely broken one; `docker compose … config` shows **no BF16
  mount** on the reasoning path.
- Deterministic gate: `uv run pytest -m "not gpu"` green; `docker compose -f
  deploy/docker-compose.fp8.yml config` no BF16 mount; `git diff --exit-code
  schemas/openapi.json` (INV-8).
- GPU: `/v1/reason` end-to-end (`GPU-AM-REASON-FP8`) + **`t2i` non-regression
  smoke** (`GPU-AM-T2I-NOREGRESS`, INV-2); VRAM trace.
- **Owner quality gate** (`OWNER-AM-REASON-QUALITY`): owner runs custom prompts,
  records PASS (INV-6). Required to promote reasoning to "verified".

### 4.5 Residency / VRAM

Reasoner is now ~quantized FP8 (est. ~8–9 GiB for the 36-layer, 4096-hidden,
Qwen3-VL-8B-class understanding tower) instead of ~26 GiB BF16 → `coresidency.py`'s
E-08 footprint doc is stale and updated; still a **separate plane, swap retained**
(INV-5). Record the OOM-free VRAM trace.

## 5. Risks & mitigations

- **[FP8 `modelopt` weights don't load / decode under a non-omni serve]** → the
  spike settles it first; small-fork-then-reprobe, else stop-and-report. No BF16.
- **[`t2i` regression from the serving-seam change]** → mandatory `t2i` smoke
  (INV-2); the reasoner is isolated in its own container, not on the omni path.
- **[Reproducibility / NFR-5: pin a *public* fork commit]** → pin an immutable
  `fengwang/vllm` commit for the reasoner image; if `33c4f35` isn't pushed public,
  flag it as a follow-up (as the omni pin was handled).
- **[Blast-radius bleed with AM-S4]** → AM-S2 does *real* container wiring; AM-S4
  finalizes the default-on merge. Keep the diff narrow; call out shared-surface
  files.
- **[Preflight relaxation weakens a real safety net]** → the new preflight still
  fails closed on a genuinely unservable source (missing weights / wrong arch);
  only the BF16-only assumption is dropped.

## 6. Scope amendment (recorded; binds this session)

Divergences from `docs/session_2_contract.yaml`, owner-authorized 2026-07-25:

1. **INV-4 hardened to absolute for reasoning:** no BF16 base *and* no bundled
   BF16 tower; the "documented BF16 exception" escape is removed. If zero-BF16 is
   infeasible, the outcome is *stop-and-report*, not a BF16 ship.
2. **Blast radius extended outside this repo** into `fengwang/vllm`
   (`the local vLLM fork (fengwang/vllm)`) — an authorized additional work
   area for a minimal, pinned fork change if the spike requires one.

All other invariants (INV-1/2/3/5/6/8) stand unchanged.

## 7. Open questions (spike-gated)

- Does plain `vllm serve` (no `--omni`) on the fork load the `fp8_blockwise_mixed`
  `modelopt` weights and decode coherent text? *(the spike)*
- If yes with no fork change → does the reasoner image reuse the omni image, or a
  dedicated fork-pinned image? *(settled during the spike/build)*
- If a fork change is needed → smallest change + is `33c4f35` public for pinning?
