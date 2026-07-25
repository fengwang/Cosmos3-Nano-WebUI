# AM-S2 Decision Record — Reasoning enabled on FP8 (zero-BF16)

Date: 2026-07-25 · Session: AM-S2 · Risk: high · Gate: `GATE-AM-S2-REASONING`
Owner quality: ✅ **Feng — OWNER-AM-REASON-QUALITY = PASS (2026-07-25)** · **GATE PASSES**
Hardware: RTX 5090 (sm_120), 32 GiB. Evidence: `docs/session_2/evidence/P1–P3`, `brainstorming.md`,
`sharded_review.md`, `adversarial_verification.md`.

## 1. TL;DR decisions
| Question | Decision | Basis |
|---|---|---|
| Can reasoning be zero-BF16 on FP8? | **YES — proven.** Non-omni `vllm serve --quantization fp8_blockwise_w8a16` decodes coherent text off the quantized understanding tower. | P2 (GPU): "4" / "…blue." / "Red, Blue, Yellow" / `80 km/h`; SSE streaming. |
| Mechanism | **Small `fengwang/vllm` fork**: register `--quantization fp8_blockwise_w8a16` (applies vllm-omni's `Fp8BlockwiseW8A16LinearMethod` to the LM MLP) + `cosmos3.py` mapper `weight_quantizer._scale`→`weight_scale`. | P1 refuted "no-fork/stock-modelopt"; P2 confirmed the fork works. |
| Reasoner runtime | **Own `vllm-reasoner` container** (residency plane, evict-before-load). | drops torch/vLLM/`WITH_REASONING` from the api image; reuses the container-plane pattern; INV-5 held. |
| BF16 | **None, anywhere on the path** (owner hardened INV-4 to absolute). | owner decision; no side-car, no bundled BF16 reasoner. |
| FP8 vs NVFP4 | **FP8 e2e now; NVFP4 → AM-S5.** | FP8-first sequencing. |
| Image / reproducibility | **COPY-patch the omni-image lineage** now; pin the public fork in AM-S4. | fork commit uncommitted; NFR-5 follow-up documented. |

## 2. What was asked (and answered)
AM-S1 left zero-BF16 reasoning unproven (omni chat = image-gen; R-15). AM-S2: **is there a zero-BF16
FP8 text path, and can it be wired + verified?** → **Yes** (P1 scoped the exact gap; P2 proved text
from a reproducible image; P3 confirmed `t2i` non-regressed; owner PASS).

## 3. Gate scorecard (GATE-AM-S2-REASONING)
Reasoning e2e on FP8, zero-BF16 ✓ (P2) · `t2i` non-regressed ✓ (P3, INV-2) · CPU suite green ✓ ·
owner quality PASS ✓ (INV-6) · no BF16 base/overlay/`WITH_REASONING` on the reasoning path ✓ (INV-4,
`docker compose … config`) · residency safety net held ✓ (INV-5) · API schema unchanged ✓ (INV-8).
Sharded review: 1 High (stale comments) **fixed**; 2 findings Failure-Arbiter-classified non-blocking
(by-design tokenizer fallback; R-11 dormant code). Adversarial verifier: **PASS** (independent).

## 4. Scope amendments (owner-authorized 2026-07-25)
1. INV-4 hardened to absolute (no BF16 exception). 2. Blast radius extended into `fengwang/vllm`
(the fork). Both recorded in `brainstorming.md §6` and honored.

## 5. Handoff
See `docs/handoff.md`: AM-S3 (action, unaffected), AM-S4 (commit/pin the fork; retire the legacy
overlay/`WITH_REASONING`/dormant subprocess; full-stack all-modes GPU smoke), AM-S5 (NVFP4 reasoning).
