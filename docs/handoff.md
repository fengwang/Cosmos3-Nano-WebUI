# Session Handoff

## State Snapshot
- **Session: AM-S5** — Extend + GPU-Verify on NVFP4. Risk high.
- **Branch:** `fea/eanble-reasoning-action-phase-5-session-5`.
- **Last commit at start:** `7288e00` (AM-S4). This session's work is **uncommitted** (owner reviews/commits, per the prior-session pattern).
- **Current status: `GATE-AM-S5-NVFP4` PASSES (fully).** All three modes are GPU-verified on NVFP4 off the
  quantized-only checkpoint (zero BF16, no offload): t2i (non-regressed, INV-2), action (all 3 modes via the
  omni video-API), reasoning (coherent W4A16 text via a bounded fork patch mirroring AM-S2). The NVFP4
  all-modes wiring is landed + CPU-green; the FP8 stack is byte-unchanged; `openapi.json` unchanged; sharded
  review + adversarial verifier PASS (`docs/session_5/`). **Owner NVFP4 quality gate = PASS** (Feng,
  2026-07-26: checked every WebUI tab on the nvfp4 container, all functions work as expected, quality very
  good) — INV-6 satisfied per-mode → all three modes GPU-verified + default-on on NVFP4 (INV-7).
  **Phase-5 finish line reached: Studio + Reasoning + Action GPU-verified + default-on on BOTH FP8 and NVFP4.**
- **Changed files (this session):**
  - **deploy:** `docker-compose.nvfp4.yml` (add the `vllm-reasoner` service + api reasoner caps), new
    `vllm-reasoner-nvfp4.Dockerfile`, new `vllm-reasoner/patch-nvfp4/{nvfp4_blockwise_w4a16_vllm,cosmos3,quantization__init__}.py`;
    `Makefile` (`up-nvfp4` stops both heavy planes); `.env.example` (nvfp4 all-modes note).
  - **tests:** new `tests/deploy/test_nvfp4_allmodes_wiring.py`; `tests/deploy/test_reasoner_context_cap_fits_model_len.py` (parametrized over both stacks).
  - **docs:** `docs/session_5/**` (brainstorming→execution_contract, specs/, evidence/P1–P2, fork_prototype_nvfp4/);
    `docs/{model_setup,evidence_map,risk_register,eval_seed_cases,handoff}.md`.
- **Checks run:** full `uv run pytest -m "not gpu"` = exit 0 (green, incl. new nvfp4 deploy tests);
  `docker compose -f deploy/docker-compose.nvfp4.yml config` (raw + `--env-file .env`) = a `vllm-reasoner`
  + no BF16 mount; `-f deploy/docker-compose.fp8.yml config` still renders; `git diff --exit-code
  schemas/openapi.json deploy/docker-compose.fp8.yml` clean; NVFP4 reasoner image **built + run** (baked
  patches) → coherent (NFR-5). GPU probes: `docs/session_5/evidence/P1–P2`; GPU idle 18 MiB after each.
- **Owner smoke + quality gate — DONE (Feng, 2026-07-26):** the owner ran `make up-nvfp4` and checked
  every WebUI tab (Studio/Reasoning/Action) — all functions work as expected, quality very good.
- **Checks NOT run:** a perf pass on the Marlin FP4 weight-only path (perf-suboptimal but usable, not a gate).

## Per-mode × per-format verification matrix (the handoff deliverable)

| Mode | FP8 | NVFP4 |
|---|---|---|
| **Studio (t2i)** | GPU-verified (`GPU-S3`); non-regressed every serving session | GPU-verified (`GPU-S3`); AM-S5 non-regress re-passed (INV-2) |
| **Reasoning** | GPU-verified + **owner PASS** (AM-S2, Feng 2026-07-25) | GPU-verified + **owner PASS** (AM-S5, Feng 2026-07-26) |
| **Action** (FD/policy/ID) | GPU-verified + **owner PASS** (AM-S3, Feng 2026-07-25) | GPU-verified + **owner PASS** (AM-S5, Feng 2026-07-26) |

**Default-on:** FP8 — all three, owner-confirmed (AM-S4). **NVFP4 — all three, owner-confirmed (AM-S5,
Feng 2026-07-26).** No mode required an INV-7 *limitation* (all three serve on 4-bit off the quantized-only
checkpoint, zero BF16). **Every cell in the matrix is GPU-verified + owner-PASS — the phase-5 goal.**

## Narrative Context
AM-S4 proved + defaulted-on the FP8 all-modes stack. AM-S5 extended it to NVFP4 — the phase's last unknown
(4-bit Blackwell kernels, S-D/R-04). Spike-led per the owner's choice: I GPU-probed each mode first. t2i +
action ran unchanged on the NVFP4 omni image (Marlin FP4, no offload); reasoning needed the AM-S2 pattern
re-applied for 4-bit — a bounded fork patch registering `--quantization nvfp4_blockwise_w4a16` that reuses
vLLM's `ModelOptNvFp4W4A16LinearMethod` on the **fused** text-path MLP (the fork's own nvfp4_blockwise
targets the unfused omni names). All three serve coherent output off the quantized-only checkpoint, zero
BF16. The wiring mirrors the FP8 shape: a separate `vllm-reasoner` service/image (not a parametrized FP8
Dockerfile — blast-radius isolation), `up-nvfp4` cold-starts + stops both heavy planes, api caps 7680.

## Decision Log
| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| Session shape | **Spike-led probes first** | implement-then-verify | owner choice; front-load the one real unknown (4-bit kernels) | interview; routing branch-and-compare |
| Reasoner effort ceiling | **Bounded / mirror AM-S2** | new-kernel-from-scratch | reuse the fork's `ModelOptNvFp4W4A16LinearMethod`; INV-7 if it failed (it didn't) | interview; design D2 |
| Reasoner image | **Separate nvfp4 image + patch** | parametrize the FP8 Dockerfile | the FP8 reasoner path is frozen-verified; a build-arg risks regressing it | design D1 |
| Quant target regex | **Fused** `language_model.model.layers.*.mlp.{gate_up_proj,down_proj}` | reuse the fork's unfused omni regex | the plain-text LM path fuses gate+up; the fork targets the omni construction names | evidence P2; EV-AM-FUSED-VS-UNFUSED-QUANT-TARGET |
| NVFP4 demo-input gap | **Documented owner decision** | edit `webui/**` / commit binaries | R-12 out of scope; INV-1 (no binaries); external-checkpoint asymmetry | evidence P1; model_setup note |

## Next Priority Queue
1. **Owner NVFP4 quality gate — DONE ✅ (Feng, 2026-07-26).** The owner checked every WebUI tab on the
   `make up-nvfp4` container — all functions work as expected, quality very good (incl. the 4-bit
   reasoning; the fused global-scale MAX-merge did not degrade it perceptibly). `OWNER-AM-REASON-QUALITY`
   + `OWNER-AM-ACTION-QUALITY` (NVFP4) = **PASS** → **`GATE-AM-S5-NVFP4` PASSES fully**; all three modes
   GPU-verified + default-on on NVFP4 (INV-6/INV-7). AM-S5 is complete.
2. **NVFP4 demo-input asymmetry — RESOLVED (2026-07-26).** The owner added the 3 missing action
   conditioning inputs (`example_action_fd_agibotworld_first_frame.png`, `example_action_id_av_0_input.mp4`,
   `example_action_id_av_1_input.mp4`, byte-identical from FP8) to `wfen/Cosmos3-Nano-NVFP4-Blockwise` in
   commit **`e59dcff…`** (assets-only; weights/config unchanged vs `5514c42b…`). The NVFP4 pin is bumped to
   `e59dcff…` in `.env.example`, `docs/model_setup.md`, AND `README.md` (line 145). The README bump is an
   **owner-authorized blast-radius amendment** (README is normally AM-S6's; the owner OK'd the SHA-only bump
   this session, Feng 2026-07-26), scoped to the pin only. The local
   `/data/models/Cosmos3-Nano-NVFP4-Blockwise/assets/` also has the files, so `make up-nvfp4`'s Action
   "Run demo" now works.
3. **AM-S6 (docs):** README "See it in action" + `docs/walkthrough.md` reflecting the real per-mode/per-format
   matrix above (now **complete** — every FP8 + NVFP4 mode is owner-PASSed as of 2026-07-26); fix the stale README
   `make up-fp8-reasoning` ref; **fix the stale README "BF16 base (reasoning + action)" checkpoint row +
   the "reasoning and action also use the BF16 base" prose (both now zero-BF16 — AM-S2/S3);** reconcile the
   BF16 license (E-14). (AM-S5 bumped only the NVFP4 pin SHA in README, nothing else.)

## Warnings And Gotchas
- **Owner `.env`:** repo-root `.env` pins `COSMOS3_NVFP4_DIR=/data/models/Cosmos3-Nano-NVFP4-Blockwise`
  (public `wfen/…` rev now `e59dcff…`). Confirm the resolved mount with `docker compose --env-file .env -f
  deploy/docker-compose.nvfp4.yml config` before trusting a run (R-11).
- **⚠ The local NVFP4 checkpoint clone git state is broken/dirty** (discovered 2026-07-26): its `.git`
  HEAD is `b5c9332` (a diverged, non-ancestor commit) with ~614k lines of uncommitted working-tree changes
  — NOT what is on HF (`main` = `e59dcff`). The on-disk *files* are the correct checkpoint content (+ the 3
  action assets), so the mounted stack is fine, but **do NOT `git commit/push` from that local clone** — the
  Action-asset publish was done via the HF API directly to `main` (bypassing the clone). For a clean tree,
  re-`hf download` at `e59dcff…` into a fresh dir. Not blocking; a hygiene note.
- **NVFP4 reasoner image must be built:** `make up-nvfp4` builds `cosmos3-nano-vllm-reasoner-nvfp4:local`
  on first up (or `docker build -f deploy/vllm-reasoner-nvfp4.Dockerfile -t cosmos3-nano-vllm-reasoner-nvfp4:local .`).
  Its heavy fork layers cache-hit from the FP8 reasoner image.
- **NVFP4 forbids layerwise offload** (Marlin FP4 repacks on CUDA after load). Do NOT add
  `--enable-layerwise-offload` to any NVFP4 service (guarded by `test_nvfp4_allmodes_wiring.py`).
- **Reasoner perf:** the W4A16 Marlin path is weight-only FP4 (no native sm_120 FP4 GEMM — vLLM warns);
  acceptable for reasoning, a perf follow-up (as W8A16 was for FP8).
- **Known failing tests:** none.
- **Files future sessions must not casually edit:** `deploy/docker-compose.fp8.yml` + the FP8
  `vllm-reasoner.Dockerfile`/`patch/` (frozen-verified); `schemas/openapi.json` (INV-8); the proven
  `vllm-omni` image + `t2i` path (INV-2); `README.md`/`docs/walkthrough.md` (AM-S6); `docs/archive/**`.

## Eval Seeds
- **Missed check (now caught):** EV-AM-QUANT-PLUGIN-IMPORT-TIMING (import-time circular import when
  registering a quant plugin); EV-AM-FUSED-VS-UNFUSED-QUANT-TARGET (fused-MLP targeting in the text path).
- **New regression tests added:** `tests/deploy/test_nvfp4_allmodes_wiring.py` (nvfp4 all-modes + no-BF16 +
  no-offload + up-nvfp4 stops both planes + FP8 offload contrast) — RED-then-GREEN this session; the
  reasoner-context-cap test now covers both stacks.
- **Instruction-update candidates:** EV-AM-NVFP4-DEMO-ASSET-ASYMMETRY, EV-AM-BOTH-STACK-RENDER-NONREGRESS,
  EV-AM-NVFP4-FUSED-GLOBAL-SCALE. All recorded in `docs/eval_seed_cases.md` (AM-S5 harvest).
