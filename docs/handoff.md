# Session Handoff

## State Snapshot
- Session: **AM-S2** — Reasoning enabled + GPU-verified on FP8, **zero-BF16**. Risk high.
- Branch: `fea/eanble-reasoning-action-phase-5-session-2`.
- Status: **GATE-AM-S2-REASONING PASSES** — reasoning runs end to end on FP8 off the
  quantized-only checkpoint (no BF16), `t2i` non-regressed, CPU suite green, owner
  reasoning-quality verdict recorded **PASS** (2026-07-25).
- Changed files (this session):
  - **repo `api/`**: `app/main.py` (reasoning branch → `ContainerPlaneWorker`),
    `orchestrator/planes.py` (`container_reasoning_spec`), `app/routes/reasoning.py`
    (`VllmReasonerStream` → reasoner container URL).
  - **repo `deploy/`**: `vllm-reasoner.Dockerfile` + `vllm-reasoner/patch/` (vendored fork
    patch), `docker-compose.base.yml` (reasoner api env), `docker-compose.fp8.yml`
    (`vllm-reasoner` service), `.env.example` (reasoner vars; BF16 overlay marked legacy).
  - **repo `tests/`**: `test_gen_engine_selection.py` (updated), `api/test_reasoner_container_wiring.py` (new).
  - **repo `docs/session_2/`**: `brainstorming.md`, `evidence/P1–P3`, `evidence/fork_prototype/`,
    `design.md`, `execution_contract.md`, `decision_record.md`, `sharded_review.md`,
    `adversarial_verification.md`; plus `docs/{evidence_map,risk_register,eval_seed_cases,handoff}.md`.
  - **vLLM fork** (`fengwang/vllm`, local working tree, **uncommitted**): new
    `model_executor/layers/quantization/fp8_blockwise_w8a16_vllm.py` + registration in
    `quantization/__init__.py` + `models/cosmos3.py` mapper fix. `fengwang/vllm-omni` **unchanged**.
- Checks run: `uv run pytest -m "not gpu"` green; `docker compose -f deploy/docker-compose.fp8.yml
  config` (no BF16 mount, `vllm-reasoner` present); `git diff --exit-code schemas/openapi.json`
  clean; **GPU-AM-REASON-FP8** (P2, from the reproducible reasoner image); **GPU-AM-T2I-NOREGRESS**
  (P3); **OWNER-AM-REASON-QUALITY** = PASS; sharded review + adversarial verifier (docs/session_2/).
- Checks NOT run: full-stack api→orchestrator→reasoner e2e (docker-socket start/stop + the
  generation↔reasoning swap) as a single GPU run — the pieces are proven (reasoner image serves text;
  CPU swap/residency tests green; factory builds the container worker) but the integrated swap is a
  candidate for the **AM-S4** all-modes smoke. NVFP4 reasoning (AM-S5). A build of the reasoner image
  from the *local fork* (I proved via the deployed-image + COPY-patch, equivalent runtime).

## Narrative Context
AM-S1 left zero-BF16 reasoning **unproven** (omni chat = image-gen; R-15). AM-S2 resolved it:
plain `vllm serve <quantized> --quantization fp8_blockwise_w8a16` (NO `--omni`, no BF16) decodes
coherent **text** off the quantized understanding tower. The enabling change is a **small
`fengwang/vllm` fork**: register a `--quantization fp8_blockwise_w8a16` config that applies the
existing vllm-omni `Fp8BlockwiseW8A16LinearMethod` (resident FP8 + JIT 128×128 dequant) to the LM
MLP projections, plus a `cosmos3.py` mapper fix (`weight_quantizer._scale`→`weight_scale`). The
earlier hope of "no fork / stock modelopt" was **refuted** (P1). Reasoning is wired as a separate
**`vllm-reasoner` container** residency plane (evict-before-load vs generation; the single-slot FSM
is unchanged), so the api image needs no torch/vLLM/`WITH_REASONING`. Owner quality: **PASS**.

## Decision Log
| Decision | Chosen | Rejected | Reason |
|---|---|---|---|
| Reasoning zero-BF16 | **Serve quantized FP8 understanding tower via a vLLM fork** (`--quantization fp8_blockwise_w8a16`) | BF16 base side-car; bundled `-dist` BF16 `reasoner/` | owner hardened INV-4 to absolute — no BF16 at all |
| Reasoner runtime | **Own container** (`vllm-reasoner`, non-omni serve) | api subprocess | drops torch/vLLM/`WITH_REASONING` from the api image; reuses the container-plane pattern |
| Fork scope | **minimal** (register quant + mapper fix; reuse the omni W8A16 method) | new kernel / big fork | the blockwise-FP8 method already existed in vllm-omni |
| Image strategy | **COPY-patch the omni-image lineage** (`deploy/vllm-reasoner.Dockerfile`) | build vLLM from the fork | fast + reproducible; pin the public fork later (AM-S4) |
| FP8 vs NVFP4 | **FP8 e2e this session** | both now | FP8-first sequencing; NVFP4 = AM-S5 |

## Next Priority Queue
1. **AM-S3 (action, FP8):** unchanged by AM-S2 — wire the omni robot policy `(a)` / fixed `(c)`.
   Note: Studio+Action can plane-merge (same omni model); reasoning is a *third* plane that swaps.
2. **AM-S4 (default-on, FP8):** finalize the reasoner wiring into the clean default —
   (a) **commit + pin** the `fengwang/vllm` fork commit and switch `deploy/vllm-reasoner.Dockerfile`
   from the vendored COPY-patch to a pinned public fork install (NFR-5); (b) remove/repoint the
   legacy BF16 `docker-compose.reasoning.yml` overlay + `WITH_REASONING` build split + the dormant
   subprocess `reasoning_spec`/`ReasonerConfig`/`reasoner_preflight` (R-11 dead code); (c) run the
   **full-stack all-modes GPU smoke** including the api-driven generation↔reasoning residency swap.
3. **AM-S5 (NVFP4):** prove reasoning on NVFP4 — the NVFP4-dist checkpoint uses `nvfp4_blockwise`;
   the same fork pattern should extend (register/select the NVFP4 W4A16 method for the text path).

## Warnings And Gotchas
- **The fork change is uncommitted** in the local `fengwang/vllm` working tree (owner to review /
  commit / push / pin). Until then, the reproducible reasoner image relies on the **vendored
  COPY-patch** under `deploy/vllm-reasoner/patch/` (kept byte-identical to the fork edit).
- **Reasoner VRAM ≈ 26 GiB** at `--gpu-memory-utilization 0.85` (KV-cache-dominated; the FP8 weights
  are far smaller). It and the ~13.5 GiB omni generation model **must never co-reside** (32 GiB
  budget) — the orchestrator's evict-before-load enforces this (INV-5); do not add a Studio+Reasoning
  plane-merge without a measured OOM-free trace.
- **W8A16 dequantizes the full weight per forward** (no fused kernel) — correct on sm_120, not
  perf-optimal; fine for reasoning, a candidate for a fused-kernel follow-up.
- The old BF16 reasoning path (`docker-compose.reasoning.yml`, `WITH_REASONING`, the subprocess
  `reasoning_spec`) is **legacy/dormant**, not on `make up-fp8`; AM-S4 removes it.

## Eval Seeds
- **EV-AM-QUANT-SIDECAR-NOT-AUTODETECTED** — the FP8 quant is in a side `quantization_config.json`
  (not `hf_quant_config.json`), so stock vLLM auto-detect + `--quantization modelopt` both fail;
  verify the quant is *applied*, not just that the server returned 200.
- **EV-AM-FUSED-QUANT-TARGET** — vLLM fuses `gate_proj`+`up_proj`→`gate_up_proj`; a quant target
  regex written for the unfused diffusion names silently misses the fused LM layer.
- **EV-AM-REASONER-CONTAINER-WIRING** — reasoning is a container plane now; subprocess/`:8765` tests
  are stale (update, never revert).
