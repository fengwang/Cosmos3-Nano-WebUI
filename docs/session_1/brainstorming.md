# AM-S1 Brainstorming — Feasibility Spike (FP8) Probe Strategy

Date: 2026-07-24
Session: AM-S1 (Phase-5 "All-Modes"), risk **high**, routing branch-and-compare.
Authority: `docs/session_1_contract.yaml` (session), `docs/project_contract.md`
(phase), `docs/prd.md` (dominant). Evidence: `docs/evidence_map.md`.

## 1. Purpose

Resolve the phase's pivotal unknowns on the RTX 5090, **FP8-only**, before any
production wiring is built:

- **S-A** — can `vllm serve --omni` on the **quantized** checkpoint answer
  `/v1/chat/completions` coherently (option (a) for reasoning)?
- **S-C** — can `vllm-omni` serve **action**, or must action use the side-by-side
  `(c)` fallback (the `diffusers_action` graft)?
- **S-E / E-06** — confirm the action-tensor gap against the *real pinned*
  checkpoint and decide the **zero-BF16 action packaging** path.
- **Residency** — does Studio+Reasoning collapse into one resident model
  (plane-merge) or must it swap (E-08 / INV-5)?

Output is an **owner-approved decision record + captured evidence**, not shipped
production code (throwaway/dev wiring is acceptable).

## 2. Session-shaping decisions (interview + brainstorming, 2026-07-24)

| # | Decision | Rationale |
|---|---|---|
| D-a | **The agent drives the live GPU probes**; owner reviews evidence and signs off in-session. | The environment is spike-ready (GPU idle, images built, checkpoints on disk, stack warm). The spike's value is empirical. |
| D-b | **Spike-lean doc set**: `brainstorming.md` + `design.md` (probe plan + rubric) + `execution_contract.md` → probes → `decision_record.md` + `sharded_review.md` + `adversarial_verification.md` + evidence/risk/eval/handoff. | Deliverable is a decision record, not code; the code-shaped ceremony (per-capability WHEN/THEN specs, TDD red-green, separate proposal/tasks/plan) has no code to bind to. |
| D-c | **Action probe depth = characterize + feasibility-load.** Prove no `(a)` action surface + actually load the `diffusers_action` `(c)` engine on GPU to prove it instantiates, but **no** quality-judged trajectory run (that is AM-S3). | `characterize the (c) fallback` per contract; a full run strays into AM-S3's owner-quality territory (out of scope). Feasibility-loading surfaces the **D1** risk as real evidence. |

## 3. Approaches considered

**① Warm-stack-first, GPU-light probes ordered first — CHOSEN.**
Reuse the warm FP8 stack. Run zero-GPU probes first (E-06 header read,
`checkpoint_prep` static eval, `-dist` prior-art), then the live ladder (§4).
*Trade-off:* efficient, orders cheap evidence before expensive GPU ops, and tests
option (a) **exactly as the PRD defines it** (same resident model serves both).
Con: sequential GPU ops cost wall-clock.

**② Isolated per-probe containers.** Spin a fresh dedicated `vllm serve --omni`
just for chat, separate from the generation stack. *Rejected* — cleaner isolation
but does **not** test "the *same* resident model serves both," which is the entire
point of option (a); it would silently answer a different question.

**③ Host-only + minimal GPU.** Infer action `(c)` loadability from CPU tests + the
D1 docs instead of a real load. *Rejected* — the owner chose feasibility-load for
action (D-c); this would under-deliver the action verdict.

## 4. Chosen probe ladder (ordered; cheap evidence first)

0. **Baseline** — CPU suite green (`uv run pytest -m "not gpu"`, already ✅ 523
   passed) and `rg action_ …/diffusers_action/loader.py` (E-06 premise in code, ✅).
1. **E-06 confirmation (no GPU)** — read the pinned `Cosmos3-Nano-FP8-Blockwise`
   `transformer/*.safetensors` header keys; assert **no** `action_*`; confirm the
   BF16 base `Cosmos3-Nano/transformer` **does** ship `action_*`.
2. **`checkpoint_prep` evaluation (no GPU)** — can `mutation`/`rewrite`/
   `safetensors_io`/`integrity_probe` express "inject `action_*` bf16 tensors +
   reconcile `action_gen` config + integrity-probe"? Examine the `-dist` variant
   (`reasoner/` subdir + `*.s5-orig.bak` surgery marks) as prior-art.
3. **Reasoning (a) probe (GPU)** — start the FP8 stack; `curl` the **existing**
   omni container `:8000/v1/chat/completions` off the quantized transformer.
   Coherent, zero-BF16 ⇒ `(a)` + plane-merge candidate.
4. **Reasoning (c) fallback probe (GPU, only if 3 fails)** — standalone
   `vllm serve` on the quantized transformer dir. Coherent ⇒ still zero-BF16 but a
   second resident ⇒ `(c)`.
5. **Action (a) surface probe (GPU)** — inspect the omni route surface
   (`/v1/models`, `/openapi.json`, `/docs`, fork endpoints) for any action
   capability. Expected: none ⇒ `(a)` excluded for action.
6. **Action (c) feasibility-load (GPU)** — attempt to instantiate the
   `diffusers_action` engine on the 5090 (graft BF16 `action_*` onto the quantized
   GEN tower; precision verify GEN=505). Loads ⇒ `(c)` viable; fails on D1 ⇒
   critical finding for AM-S3. **No** quality-judged run.
7. **VRAM traces (GPU)** — `nvidia-smi` peak at each residency state.

## 5. Pre-registered decision rubric (skeleton — the anti-conflation safeguard)

Written **before** probing so "loaded" is never recorded as "works." Full form in
`design.md`.

- **Reasoning:** `(a)` iff existing omni container returns a non-empty, on-topic,
  grammatical completion off the quantized transformer with **zero BF16** →
  plane-merge candidate. Else `(c)-zeroBF16` if a standalone quantized reasoner is
  coherent. Else `(c)-BF16 / blocked` (explicit owner decision). The **coherence
  bar** (syntactically valid, on-topic, non-degenerate) is *not* the **quality
  bar** (owner's AM-S2 gate).
- **Action:** `(a)` only if omni exposes a working action route (expected none →
  excluded). Else `(c)` = `diffusers_action`: `(c)-loads` (viable for AM-S3) **or**
  `(c)-blocked-by-D1` (critical).
- **Zero-BF16 action packaging:** E-06 confirmed → `bundle-via-checkpoint_prep
  (go)` if the toolkit can express the mutation + integrity check, else
  `alternative` (e.g. explicit-owner-decision BF16 side-car, or custom export) +
  rationale.
- **Residency:** `(a)` → VRAM trace must show chat-serving stays in the 32 GiB
  budget alongside generation (or is literally the same model → no extra VRAM);
  `(c)` → reasoner is now ~quantized, so `coresidency.py`'s ~26 GiB BF16 assumption
  (E-08) is **stale** — flag for AM-S2/S4.

## 6. Risks surfaced during brainstorming

- **Feasibility↔quality conflation** (adversarial case #1) → mitigated by the
  pre-registered coherence-vs-quality bar (§5).
- **Drift D1** (`docs/model_setup.md` §6–§7): the in-process `diffusers_action`
  engine may not load the current public checkpoint → probe 6 may fail; that is a
  *finding*, not a spike failure. It reshapes AM-S3.
- **`-dist` prior-art confusion**: the `-dist`/`-local` variants are owner
  experiments, **not** the pinned public checkpoint. E-06 is confirmed against the
  *pinned* checkpoint (probe 1); `-dist` is examined only as packaging prior-art.
- **Owner sign-off is a human gate** (D-a): the agent produces everything up to
  sign-off; the gate closes only on Feng's explicit approval.

## 7. Out of scope (reaffirmed)

Production wiring (AM-S2/S3); NVFP4 (AM-S5); the owner's output-**quality** verdict
(AM-S2/S3); editing `README.md`/`docs/walkthrough.md`/`webui/**`; committing any
re-exported checkpoint or weights; modifying `tools/checkpoint_prep/**` (evaluated,
not modified) or any `api/**`/`deploy/**` file.
