# AM-S1 Decision Record — Feasibility Spike (FP8)

Date: 2026-07-24 · Session: AM-S1 · Risk: high · Gate: `GATE-AM-S1-SPIKE`
Owner sign-off: ✅ **Feng — approved 2026-07-24** (see §8) · **GATE-AM-S1-SPIKE PASSES**
Evidence: `docs/session_1/evidence/P1`–`P7`. Hardware: RTX 5090 (sm_120), 32 GiB,
driver 610.43.03. Checkpoint: `wfen/Cosmos3-Nano-FP8-Blockwise` (deployed on-disk
`4e181f9`; pinned public `9bf5d6ae` cross-checked on HF). CPU baseline: green
(523 passed), unchanged. No production code or checkpoint modified.

## 1. TL;DR decisions

| Question | Decision | Confidence / basis |
|---|---|---|
| **Reasoning `(a)` vs `(c)`** | **`(c)` — side-car reasoner.** The omni server does **not** serve text reasoning. | High (P3: `/v1/chat/completions` returns images, not text; no request-level text path). |
| **Zero-BF16 reasoning** | **UNRESOLVED → explicit owner decision.** No zero-BF16 reasoning path found this spike. | High that it's unproven; the path (if any) is an AM-S2 investigation. |
| **Action `(a)` vs `(c)`** | **Verdict: neither functional as-served** ((a) surface present-but-unwired; (c) collides). **AM-S3 target: `(a)`**; `(c)` = code-fixed fallback. | High (P5). |
| **Zero-BF16 action packaging** | **`bundle-via-checkpoint_prep` — GO, and ALREADY APPLIED (P6-S5).** No re-export needed. | High (P1+P2: adapters bundled in pinned+deployed checkpoints; tool + sidecar stamp). |
| **E-06 (action-tensor gap)** | **CORRECTED: gap was real at raw-quantization, closed by P6-S5; no gap on current checkpoints.** | High (P1: 5 `action_*` present at both revisions; P2: P6-S5 mutate stamp). |
| **Residency** | **Studio+Action *can* plane-merge (same omni model — projected); Reasoning stays a separate plane (swap; E-08 BF16-reasoner math still holds today).** | Med-High (P7; the wired-merge footprint is unmeasured). |

## 2. What the spike asked (and answered)
1. Can `vllm-omni` serve **reasoning** off the quantized checkpoint (option a)? → **No**
   (its chat is image generation).
2. Can `vllm-omni` serve **action**, or must it use `(c)`? → **Surface exists but is
   unwired**; `(c)` in-process graft is broken; neither works as-served today.
3. Confirm E-06 + decide zero-BF16 action packaging. → **E-06 corrected** (no gap);
   packaging **already done** via `checkpoint_prep mutate`.
4. Residency implication. → **Studio+Action merge candidate; reasoning swaps.**

## 3. Reasoning — decision `(c)`; zero-BF16 UNRESOLVED
**Evidence (P3):** the standalone omni server (identical to the deployed FP8
command) exposes `/v1/chat/completions`, but every text prompt returns a **single
image** (`completion_tokens=1`, `content:[{image_url…}]`). `response_format:text`
→ still an image; `modalities:[text]` → HTTP 500 image-gen error. The checkpoint
ships a Qwen3 text chat template, but the serving binds chat to image generation and
exposes no output-modality selector. This reproduces E-05 ("reasoning not working").

**Decision:** reasoning mechanism is **`(c)`** — a side-by-side reasoner the
orchestrator swaps in (as today, E-04). **Zero-BF16 reasoning is UNRESOLVED**: the
omni path will not yield text, and no separate quantized-text-tower serving was
proven. **Owner decision required (INV-4):** either (i) fund an AM-S2 investigation
to elicit text from the omni/understanding tower (fork modality flag, or serving the
quantized text tower on another engine) — unproven; or (ii) accept a **BF16 reasoner
side-car** as an explicit, documented exception to the zero-BF16 hard goal.

## 4. Action — `(a)` targeted / `(c)` fallback-after-fix; zero-BF16 DONE
**Evidence (P5/P6):**
- **(a):** the omni server registers `/v1/realtime/robot/openpi` (WebSocket; HTTP
  101 upgrade succeeds, bogus route → 404) — so action **is** an omni surface
  (contradicting E-07). But on connect it returns `{"error":"Robot policy not
  available","code":"unsupported"}` → the policy is **not wired** in this config.
- **(c):** the real `diffusers_action.merge_state_dicts` raises `ValueError: action
  graft key collision` on the 5 action keys — the in-process graft assumes E-06's
  gap that no longer exists (checkpoint already has the tensors). Plus
  `GEN_TOWER_QUANTIZED=505` ≠ actual 216. **`(c)` is broken as-coded.**

**Rubric verdict:** **neither (a) nor (c) is functional as-served** — the (a)
surface is present-but-unwired and (c) fails at a **CPU-side key collision** (before
the precision check), a state outside the design's enumerated action rows (see §7.1).
**Recommendation (AM-S3 target):** **`(a)`** (wire the omni robot policy to the
checkpoint's own action weights — keeps one resident model, enables Studio+Action
plane-merge); keep **`(c)`** as the pre-authorized fallback (R-02) **but only after
a code fix** (drop the base graft; use the checkpoint's tensors; fix the precision
constant). **Zero-BF16 action is already achieved at the checkpoint level** (§5) —
AM-S3's action work is **serving-path**, not packaging. Output **quality** remains
the AM-S3 owner gate (not judged here).

## 5. Zero-BF16 action packaging — GO (already applied)
**Evidence (P1/P2):** all quantized checkpoints (FP8 deployed, FP8 pinned-public
`9bf5d6ae`, NVFP4) ship the 5 BF16 `action_*` adapters with `action_gen:true` (real
non-zero values byte-verified on the **deployed FP8**; keys+dtype+shape confirmed on
`9bf5d6ae` and NVFP4). `tools/checkpoint_prep mutate` ("append action tensors +
restore BF16 lm_head", P6-S5) is the packaging tool — validated (dtype+shape,
refuses double-apply), with a **unit-tested integrity-probe path**,
backup/restore-safe. The deployed checkpoint's `quantizer_map_diff.json` carries the
P6-S5 stamp (`n_weight_quantized:216`, `appended_action_keys`=the 5,
`lm_head_restored_bf16:true`). *Attribution caveat:* the "applied via P6-S5 mutate"
claim rests on that sidecar provenance + touched-files + `.s5-orig.bak`, **not a
re-run this session**; the byte-verified, load-bearing fact is that the adapters are
**present with real values** (P1).

**Decision:** the zero-BF16 action packaging path is **`checkpoint_prep mutate` —
GO and DONE**. No new re-export is required for action. For AM-S3/NFR-5: confirm the
public pinned revision is `integrity_probe`-clean and recorded in
`docs/model_setup.md` (it already carries the adapters), and re-verify `t2i` at that
revision.

## 6. Residency implication
**Evidence (P7):** omni generation server resident ≈ **13.2–13.5 GiB / 32**; idle
18 MiB; no leak after stop. Built-in `/v1/omni/sleep|wakeup` (staged) exists.
- **Studio + Action:** if action `(a)` is wired, both are the **same resident omni
  model → plane-merge (no extra VRAM, no swap).** This is the genuine merge
  opportunity — **Studio+Action**, not the Studio+Reasoning merge the blueprint
  speculated (R-08).
- **Reasoning:** not served by omni → **separate plane, swap retained**
  (evict-before-load, INV-5). `coresidency.py`'s ~26 GiB BF16-reasoner assumption
  (E-08) is stale only if a quantized reasoner is ever achieved; today's BF16
  reasoner keeps the swap math.

## 7. Corrections to the blueprint (honesty pass)
These spike findings supersede blueprint premises (to be reflected in
`evidence_map.md`/`risk_register.md`):
- **E-06** (action-tensor gap): the gap existed *at raw quantization* but was
  **closed by P6-S5** `checkpoint_prep mutate`; the current pinned+deployed
  checkpoints **ship** the action adapters. E-06 is no longer a live blocker.
- **R-01** (zero-BF16 action blocked by checkpoint): **resolved** — action adapters
  are bundled. Residual is a *code* reconciliation (R-11-adjacent), not packaging.
- **E-07 / S-C** (action not an omni surface): **partially contradicted** — an omni
  robot surface exists (`/v1/realtime/robot/openpi`), though unwired.
- **S-A** (omni chat serves coherent reasoning): **false for text** — it serves
  images. Zero-BF16 reasoning is the new open risk (raise a risk row).
- **Drift D1** confirmed for the in-process loader (`505` vs `216`,
  revision-independent).

### 7.1 Rubric deviations (frozen rubric vs. findings)
The pre-registered rubric (design.md) is the anti-conflation safeguard; where the
findings overtook its frozen branches, the verdict is an **evidence-driven update**,
recorded here so it is not mistaken for a rubric cell:
- **E-06:** the design gate ("confirmed iff pinned-FP8 has none / base has them")
  **failed** (pinned FP8 has 5) → E-06 **refuted**, not confirmed.
- **Packaging:** the "GO" branch's precondition was "P1 gap confirmed"; P1
  *contradicted* the gap. "GO/DONE" is justified by the gap being **already closed**
  (P6-S5) — a case the rubric did not enumerate.
- **Action:** the rubric offered (a) / (c)-loads / (c)-blocked-by-D1; the real state
  is **(a)-surface-present-but-unwired** + **(c)-blocked-by-collision** (D1 is
  secondary) — a fourth, unlisted state.
- **Residency:** the rubric's two-resident row assumed "reasoner ~quantized ⇒ E-08
  stale"; the reasoner **stays BF16**, so **E-08 is not stale today** (it becomes
  stale only if a quantized reasoner is later achieved).

## 8. Handoff + owner sign-off

**For AM-S2 (reasoning):** mechanism `(c)`. Zero-BF16 reasoning is unproven — start
with the omni/understanding-tower text investigation; the fallback is an explicit
BF16 reasoner side-car (owner-decided). Do **not** assume AM-S1 produced reasoning
wiring — it did not. **AM-S1 does NOT fold into AM-S2.**

**For AM-S3 (action):** zero-BF16 packaging is done. Do serving-path work off the
checkpoint's own action weights — prefer `(a)` (wire the omni robot policy;
plane-merge with Studio), else fix `(c)` (`loader.py` must stop grafting from base
and drop the stale `505` constant). Full trajectory quality is the AM-S3 owner gate.

**Owner decisions (recorded 2026-07-24):**
1. Reasoning zero-BF16: **investigate the omni text-tower first** in AM-S2 (elicit
   text from the quantized understanding tower via a fork modality flag or a
   separate text-tower serving); fall back to a **documented BF16 reasoner side-car
   (INV-4 exception)** only if that investigation fails. → **owner: investigate first.**
2. Action target: **`(a)` omni robot policy** wired to the checkpoint's own action
   weights (enables the Studio+Action plane-merge), with the fixed `(c)` graft as the
   pre-authorized fallback. → **owner: `(a)` + `(c)` fallback.**
3. E-06/R-01/E-07/S-A corrections accepted into `evidence_map`/`risk_register`. →
   **owner: accepted.**

**Owner sign-off:** ✅ **Feng — approved 2026-07-24. GATE-AM-S1-SPIKE PASSES.**
