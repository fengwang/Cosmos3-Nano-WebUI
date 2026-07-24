# Project Contract - All Modes, GPU-Verified, Default-On

Date: 2026-07-24
Status: Active blueprint (revised output of a two-pass compilation)

Compilation: two-pass. The first pass drafted from the owner's requirement and
interview (2026-07-24), repository evidence gathered by direct inspection
(`api/app/main.py`, `api/orchestrator/planes.py`, `api/engines/vllm/coresidency.py`,
`api/engines/diffusers_action/loader.py`, `api/engines/vllm_omni/endpoints.py`,
`api/app/routes/action.py`, `deploy/**`, `Makefile`, `.env.example`,
`docs/model_setup.md`, `README.md`, and the WebUI investigation), and the archived
phase-1/2/3/4 packs. The second pass, an independent adversarial spec review,
found and resolved eight substantive issues a naive transcription of the request
would have shipped:

1. **Zero-BF16 written as an unbacked MUST.** "The stacks serve all modes off
   quantized-only weights" states an *outcome* whose feasibility is unproven —
   for reasoning (does `vllm serve --omni` chat off a quantized transformer, and
   is 4-bit NVFP4 quality acceptable) and, decisively, for action (see item 2).
   The evidence-map rule forbids promoting a speculative claim to MUST. Resolved:
   zero-BF16 is a **hard goal + owner decision**; the MUST is "*target* zero-BF16
   and never silently reintroduce BF16" plus a **feasibility gate** (`AM-S1`) and
   per-mode owner quality gates. `docs/evidence_map.md` §B marks S-A..S-E
   spike-gated; none becomes a MUST until its gate passes.
2. **The action-tensor checkpoint gap was invisible in the request.** "Enable
   action off the quantized checkpoint" assumes the quantized checkpoint can serve
   action. It cannot: it ships **without** action tensors, and the graft reads
   bf16 `action_*` adapters from the BF16 base, raising `FileNotFoundError` if
   absent (`docs/evidence_map.md` E-06). Resolved: zero-BF16 action is scoped as a
   **checkpoint-packaging** task (bundle the small bf16 adapters into the
   quantized export, plausibly via `tools/checkpoint_prep/`, re-pin a revision,
   re-verify `t2i`), tracked as `R-01`, and made explicit in `AM-S1`/`AM-S3`.
3. **Option (a) assumed to cover action.** `vllm-omni` is an OpenAI server, so
   reasoning (chat) is natural; robot action is **not** a standard OpenAI surface.
   A naive plan assumes one mechanism for both. Resolved: `AM-S1` tests reasoning
   and action **separately**; the side-by-side `(c)` fallback is pre-authorized
   for action; the contract never assumes `(a)` for action (`R-02`, S-C).
4. **`t2i` regression under serving-path churn.** `t2i` is the *only*
   GPU-verified path and it runs through the very container the phase will modify.
   A naive plan would not re-verify it each time. Resolved: `INV-2` +
   a mandatory `t2i` smoke (FP8 and, from `AM-S5`, NVFP4) as a blocking gate in
   every serving-path session (`R-05`, NFR-3).
5. **Diffusers-`t2v` quality trap.** Any move toward "one engine" risks routing
   `t2v` through `diffusers`, whose output the owner has rejected. Resolved:
   `INV-3` forbids `diffusers` for `t2v`/`i2v`/`t2v_audio`; option (b) is excluded.
6. **Default-on before verified.** Merging the stacks and flipping modes on by
   default before they run would ship broken defaults. Resolved: enable+verify
   each mode (`AM-S2`/`AM-S3`) **before** the default-on wiring (`AM-S4`);
   `INV-7` gates default-on on the mode having passed (`R-07`).
7. **Co-residency / VRAM assumption drift.** `coresidency.py`'s budget math is
   premised on a ~26 GiB BF16 reasoner; zero-BF16 makes the reasoner ~quantized,
   and option (a) could even collapse Studio+Reasoning into one resident model
   (no swap). A naive plan leaves the stale assumption or over-claims co-residency.
   Resolved: `INV-5` preserves the evict-before-load safety net and treats any
   co-residency/plane-merge as an **explicitly verified** optimization, not an
   assumption (`R-08`).
8. **Docs written before the modes run.** "Expected outputs" and screenshots for
   reasoning/action cannot be truthful before a real, quality-approved run.
   Resolved: `AM-S6` runs **last**; `docs/walkthrough.md` placeholders are filled
   by the owner post-verification; the honesty invariant governs the status table
   (`R-06`/`R-13`, `INV-6`).

This document is the revised output only.

Authority chain: read this file before implementing any phase-5 (`AM`) session.
Session-specific authority comes from `docs/session_{n}_contract.yaml`. If a
session contract conflicts with this file, stop and record the conflict before
editing.

## 1. Objective

Make Studio, Reasoning, and Action actually run on a single RTX 5090 and be on by
default in both the `fp8` and `nvfp4` stacks, each serving all modes from the
quantized-only checkpoint (zero BF16), with the orchestrator swapping residency on
demand — while keeping the one already-verified path (`vllm-omni` `t2i`)
non-regressed and the project honest about what has actually been verified.
Deliver this as a documentation blueprint: six session contracts and their gates,
executed later one at a time.

## 2. Hard Commitments

1. **Phase identity:** session contracts are `AM-S1`..`AM-S6`; deliverables live
   at `docs/` root. Gates are `GATE-AM-S{1..6}-*`.
2. **Documentation-only blueprint:** this pass writes only `docs/**`. No
   application code, config, `README.md`, `docs/walkthrough.md`, or non-doc
   content is edited until a later session executes its contract.
3. **Finish line:** a mode is "done" only when it runs end to end on the RTX 5090
   **and** the owner's manual quality gate passes **and** it is enabled by default
   in the stacks where it passed.
4. **Zero-BF16 target, no silent BF16:** the default `fp8`/`nvfp4` stacks bring up
   all three modes with **no** BF16 base mount, **no** reasoning overlay, and
   **no** `WITH_REASONING` build. Any BF16 dependency that a session cannot remove
   is surfaced as an explicit, documented owner decision at that session's gate —
   never left as a silent default.
5. **Serving strategy fixed:** try option (a) (`vllm-omni` serves reasoning/action)
   first; fall back to option (c) (side-by-side backends the orchestrator swaps)
   only where (a) is infeasible. Option (b) (`diffusers`-consolidated generation)
   is excluded.
6. **`t2i` is protected; `t2v` is quantized-only:** the `vllm-omni` `t2i` path
   (FP8 + NVFP4) stays GPU-verified end to end after every change; `t2v`/`i2v`/
   `t2v_audio` are served only by the quantized `vllm-omni` path. `diffusers` is
   never used for `t2v`.
7. **Verify before default-on:** per-mode enablement + verification (`AM-S2`/
   `AM-S3`) precedes the default-on orchestration merge (`AM-S4`); a mode is
   enabled by default in a stack only after passing that stack's gate.
8. **Vertical, FP8-first:** the full all-modes pipeline is proven on FP8
   (`AM-S1`..`AM-S4`) before NVFP4 (`AM-S5`).
9. **Honesty is preserved, not relaxed:** no mode is documented "GPU-verified"
   beyond what actually ran and passed the owner's gate, per format and per mode;
   no hook/benefit/example implies an unverified mode is verified.
10. **Archive + reproducibility boundaries:** `docs/archive/**` is not edited;
    weights are never committed; any re-exported checkpoint is pinned to a new
    immutable revision recorded in `docs/model_setup.md`, with `t2i` re-verified
    against it.

## 3. Invariants

- **INV-1:** No secret, token, private host, private absolute path, model weight,
  or generated-media binary is committed as part of this work. `docs/walkthrough.md`
  image placeholders are markdown links to `docs/images/…`; no image binary is
  added by the sessions (the owner adds images later).
- **INV-2 (protect `t2i`):** the `vllm-omni` text→image path remains GPU-verified
  end to end (FP8 and, from `AM-S5`, NVFP4) after every serving-path change. Each
  such session re-runs the `t2i` smoke and records the result; a regression blocks
  the gate.
- **INV-3 (no diffusers `t2v`):** `t2v`/`i2v`/`t2v_audio` are served only by the
  quantized `vllm-omni` path; the `diffusers` engine is never used for them
  (owner quality constraint). Option (b) is out of the design space.
- **INV-4 (zero-BF16, no silent fallback):** the default stacks require no BF16
  base, no reasoning overlay, and no `WITH_REASONING` build; verifiable by
  `docker compose … config` (no BF16 mount) and the default build args. Any BF16
  use is an explicit owner decision recorded at a gate.
- **INV-5 (residency safety net):** the evict-before-load single-slot discipline
  is preserved — VRAM stays within the 32 GiB budget, and a different-residency
  request preempts. Any co-residency or plane-merge (e.g. Studio+Reasoning sharing
  the `vllm-omni` container) is adopted only with recorded VRAM-trace evidence that
  it stays OOM-free; it is never assumed.
- **INV-6 (honesty / verification):** a mode is documented "GPU-verified" only
  after (i) a recorded end-to-end run on the RTX 5090 and (ii) the owner's recorded
  manual quality PASS — per format, per mode. Neither alone suffices.
- **INV-7 (honest default-on):** a mode is enabled by default in a given stack
  only after it passes that stack's GPU + owner gate; a mode/format that fails is
  documented honestly (not hidden, not over-claimed) and is not silently enabled.
- **INV-8 (stable API surface):** public API request/response schema shapes
  (`schemas/openapi.json`) do not change unless a session contract explicitly
  authorizes it and re-runs the schema-sync gate; the WebUI already targets these
  endpoints.
- **INV-9 (feasibility is gated):** the load-bearing feasibility claims (S-A..S-E)
  are spike-gated and speculative until proven on hardware; they cannot be written
  as shipped capabilities or MUSTs before their gate passes.

## 4. Gates

- **GATE-AM-S1-SPIKE:** on the RTX 5090 against the FP8 quantized checkpoint,
  recorded evidence for (a) whether `vllm serve --omni` answers
  `/v1/chat/completions` coherently; (b) whether action can be served by
  `vllm-omni` or needs the `(c)` fallback; (c) confirmation of the action-tensor
  gap (E-06) and a decision on the zero-BF16 action packaging path (bundle via
  `tools/checkpoint_prep/` vs alternative). Output: a per-mode `(a)`/`(c)` decision
  and a packaging decision, **owner-approved**. No production code need ship; a
  throwaway/dev wiring is acceptable for the spike.
- **GATE-AM-S2-REASONING:** reasoning runs end to end on the FP8 stack off the
  **quantized-only** checkpoint (no BF16 mount / overlay / `WITH_REASONING`); the
  `t2i` smoke re-passes (INV-2); the CPU suite (`uv run pytest -m "not gpu"`) is
  green; the owner's manual reasoning-quality verdict is recorded **PASS** (INV-6).
- **GATE-AM-S3-ACTION:** action runs end to end on the FP8 stack off a
  quantized-only checkpoint (adapters bundled, or the `AM-S1` fallback with any
  residual BF16 dependency an explicit owner decision, INV-4); if a checkpoint was
  re-exported, a new revision is pinned and `t2i` re-verified against it (NFR-5);
  the `t2i` smoke re-passes; CPU suite green; owner action-quality verdict
  recorded **PASS**.
- **GATE-AM-S4-ORCHESTRATION:** a plain `make up-fp8` brings up all three modes;
  the reasoning overlay dependency and the `WITH_REASONING` default split are
  removed; `Makefile`, `.env.example`, `deploy/**`, and `docs/model_setup.md` are
  reconciled to require no BF16 base; `docker compose -f deploy/docker-compose.fp8.yml
  config` shows no BF16 mount and an all-modes wiring; a full all-modes GPU smoke
  passes on FP8; `t2i` non-regressed; CPU suite green.
- **GATE-AM-S5-NVFP4:** the `AM-S4` all-modes design is extended to NVFP4 and each
  mode is GPU-verified on NVFP4 (owner quality PASS) or its residual limitation is
  an explicit, documented owner decision (INV-7); `t2i` (NVFP4) non-regressed;
  default-on applies only to modes that passed.
- **GATE-AM-S6-DOCS:** the README carries a "See it in action" section and links a
  `docs/walkthrough.md` with per-mode example input → expected output and
  `docs/images/…` placeholders; the README per-mode verification status is a subset
  of what actually passed (INV-6); the BF16-license discrepancy (E-14) is
  reconciled in `docs/model_setup.md`; every internal link resolves; no image
  binary is committed; the honesty pass finds no surviving over-claim.

## 5. Session Routing

Risk classification follows the requested risk router. Model/data-pipeline and
dependency changes are **high risk**, so every enablement session (`AM-S1`..
`AM-S5`) routes with independent verification and the owner's human decision gate.

| Session | Risk | Routing | Human gate |
|---|---|---|---|
| AM-S1 Feasibility spike (FP8) | high | branch-and-compare (option a vs c, per mode) + evidence capture | **Yes** — owner approves the `(a)`/`(c)` + packaging decision |
| AM-S2 Reasoning on FP8 (zero-BF16) | high | worker + sharded review + adversarial verifier + independent `t2i`-non-regression check | **Yes** — owner reasoning-quality verdict |
| AM-S3 Action on FP8 (zero-BF16) | high | worker + sharded review + adversarial verifier; checkpoint-repackaging integrity-probed | **Yes** — owner action-quality verdict |
| AM-S4 Orchestration + default-on (FP8) | high | worker + sharded review + adversarial verifier; full all-modes smoke | **Yes** — owner confirms the default `make up-fp8` all-modes run |
| AM-S5 Extend + verify on NVFP4 | high | branch-and-compare per mode (a/c; kernel fallback) + adversarial verifier | **Yes** — owner per-mode NVFP4 quality verdict |
| AM-S6 README + walkthrough docs | low | single agent + deterministic checks + one review, **plus a mandatory adversarial no-over-claim / no-lost-caveat honesty pass** | Recommended owner read of the rendered README/walkthrough |

`AM-S6` is low risk (docs) but carries the same explicit honesty pass phase-4's
`LX-S2` used, because promoting modes to "verified" is exactly the over-claim
hazard (`R-06`).

## 6. Change Control

- Do not edit outside a session contract's `blast_radius.allowed_files`.
- Do not consolidate generation onto `diffusers`, and do not use `diffusers` for
  `t2v`/`i2v`/`t2v_audio` (INV-3).
- Do not enable a mode by default before it passes its GPU + owner gate (INV-7).
- Do not mark a mode "GPU-verified" without the recorded run **and** owner quality
  PASS (INV-6).
- Do not reintroduce a BF16 base into the default path without an explicit,
  recorded owner decision (INV-4).
- Do not change a public API route shape or `schemas/openapi.json` unless the
  session contract authorizes it (INV-8).
- Do not commit weights, generated media, or images; `docs/walkthrough.md` uses
  placeholders (INV-1).
- Do not silently replace a checkpoint revision; a re-export pins a new revision,
  records it in `docs/model_setup.md`, and re-verifies `t2i` (NFR-5).
- Do not edit `docs/archive/**`; do not change network binding, auth, or the
  guardrails posture.

## 7. Verification Policy

- Classify failures before fixing: BUG, SPEC_GAP, AMBIGUITY, ENVIRONMENT, or
  TEST_BUG (`docs/agent_workflow/prompts/failure_arbiter.md`).
- Prefer deterministic, host-runnable evidence where possible: `uv run pytest -m
  "not gpu"` for the CPU suite; `docker compose … config` for the zero-BF16 wiring
  assertion; `rg` sweeps for removed overlay/`WITH_REASONING`; the checkpoint
  `integrity_probe` for any re-export.
- GPU verification is required this phase (unlike phase-4): each enablement session
  runs its mode(s) end to end on the RTX 5090 and records the standard evidence
  fields; the `t2i` non-regression smoke is a blocking gate on every serving-path
  session (INV-2, NFR-3).
- Output **quality** is the owner's manual gate (Decision 6); it is recorded as a
  verdict with the example prompts used, not asserted by a deterministic check.
- Claims in user-facing docs must point to an evidence row in
  `docs/evidence_map.md` or be phrased as a limitation (INV-6).

## 8. Done Condition

The phase-5 (`AM`) blueprint's session set is done when `GATE-AM-S1-SPIKE` through
`GATE-AM-S6-DOCS` all pass; all three modes are GPU-verified (owner quality PASS)
and default-on in every stack/format where they passed; the default stacks require
no BF16 base (INV-4); the `vllm-omni` `t2i` path is non-regressed on both formats
(INV-2); and `docs/evidence_map.md`, `docs/risk_register.md`, and
`docs/eval_seed_cases.md` reflect the final per-mode, per-format state — including
any explicit owner decision where a mode/format could not reach zero-BF16 or could
not be served on NVFP4, recorded honestly rather than hidden.
