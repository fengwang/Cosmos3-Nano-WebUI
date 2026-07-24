# PRD - All Modes, GPU-Verified, Default-On (Studio + Reasoning + Action)

Date: 2026-07-24
Status: Draft blueprint (revised after adversarial review), documentation first
Owner: Feng
Phase: 5 ("AM" — All-Modes). Session IDs `AM-S1`..`AM-S6`.
Related: `docs/project_contract.md`, `docs/evidence_map.md`,
`docs/risk_register.md`, `docs/eval_seed_cases.md`,
`docs/session_{1..6}.md`, `docs/session_{1..6}_contract.yaml`. Prior phases are
archived under `docs/archive/phase-1/` (migration, `MIG-S*`),
`docs/archive/phase-2/` (GPU release readiness, `GPU-S*`),
`docs/archive/phase-3/` (UX simplification / trusted-LAN posture, `UX-S*`), and
`docs/archive/phase-4/` (single-GPU comfort + ADHD README, `LX-S*`); they are
prior-art input to this blueprint and are not edited by this phase.

## 1. Problem

Cosmos3-Nano-WebUI advertises three modes, and its Web UI already ships a
complete, first-class tab for each — **Studio** (generation: `t2i`/`t2v`/`i2v`/
`t2v_audio`), **Reasoning** (`/v1/reason`, a streaming chat surface), and
**Action** (robot `forward_dynamics`/`inverse_dynamics`/`policy` with a 3D URDF
viewer) (`docs/evidence_map.md` E-12). But only **one** of those modes actually
works end to end on a GPU, and the other two are not reachable at all from the
default deployment:

- **Only text→image is GPU-verified.** `t2i` is verified end to end on FP8 and
  NVFP4 through the `vllm-omni` container (`GPU-S3`, E-11). Every other mode is
  documented "implemented · CPU-tested · GPU gate (`MIG-S8`)" — never actually
  run on the target hardware.

- **Reasoning is not runnable in the default stack.** Reasoning runs as a
  **separate `vllm serve` subprocess** (port 8765, its own `/health` probe)
  pointed at the **BF16 base** model, and it exists only when the API image is
  built with `--build-arg WITH_REASONING=1` **and** the optional
  `docker-compose.reasoning.yml` overlay is layered on via `make up-fp8-reasoning`
  (E-04/E-05). A plain `make up-fp8` ships **no reasoner at all**. The owner
  confirms that even the overlay path does not currently yield working reasoning
  — matching the "not actually possible" report that motivated this phase.

- **Action is only implemented under a dormant engine.** Action is grafted into
  the **in-process `diffusers` generation engine** (`gen_worker`), which is
  **not** the default. The default generation engine is `vllm_omni` (the
  container), whose action-serving path is unverified and likely absent (E-07).
  Worse, the action graft reads its `action_*` adapter tensors **from the BF16
  base transformer** and **raises `FileNotFoundError` if they are absent** — the
  quantized `*-Blockwise` checkpoints ship **without** action tensors (E-06).

- **Three deploy stacks, none of which is "all modes."** Today there are two
  generation stacks (`docker-compose.fp8.yml`, `docker-compose.nvfp4.yml`, each
  `include:`-ing the base) plus a third reasoning overlay; `make up-fp8`,
  `make up-nvfp4`, and `make up-fp8-reasoning` are three different postures, and
  none of them brings up Studio + Reasoning + Action together (E-10).

The result is a project whose UI promises three capabilities while its default
deployment delivers one, and whose "implemented · CPU-tested" language is more
generous than the deployable reality.

### 1.1 Framing correction (adversarial pass)

The originating request — "enable all modes in one stack; the container
auto-switches backend models on demand" — is sound in spirit but hides three
facts a naive transcription would miss:

1. **Model switching already exists** where the modes are homogeneous: the
   orchestrator is a single-slot residency FSM (`Plane.GENERATION` vs
   `Plane.REASONING`) that evicts-before-loads via a process kill and lets a
   different-residency request preempt immediately (E-08/E-09/E-16). The work is
   not "invent swapping"; it is to make all three modes *reachable and verified*
   off a single quantized checkpoint and to *simplify* the deploy surface.
2. **"Zero-BF16" is easy for reasoning and hard for action.** Reasoning is a
   language-model surface (`/v1/chat/completions`) that `vllm serve --omni`
   natively speaks, and the quantized checkpoint is self-contained with a chat
   template (E-02/E-03); pointing the reasoner at the quantized transformer is
   *plausible*. Action, however, needs adapter tensors that **do not exist in
   the quantized checkpoint** (E-06) — so "zero-BF16 action" is a
   **checkpoint-packaging** problem (bundle the small bf16 `action_*` adapters
   into the quantized export, plausibly via `tools/checkpoint_prep/`, E-13/E-17),
   not merely a serving-config change.
3. **"Verified" is exactly where over-claiming lives.** The deliverable is to
   promote modes to "GPU-verified"; the phase-3 docs review already caught a
   false-verification claim once. Promotion therefore requires the owner's
   **manual quality gate on the target hardware**, per format and per mode — not
   a single successful invocation (E-11, and the honesty precedent in
   `docs/archive/phase-3/` / `docs/archive/phase-4/`).

## 2. Goal

Make all three modes — **Studio, Reasoning, Action** — actually run on the
owner's RTX 5090 and be **on by default** in **both** the `fp8` and `nvfp4`
stacks, each serving *all* modes from the **quantized-only checkpoint (zero
BF16)**, with the container auto-switching backend residency on demand.

Concretely:

- Prefer **option (a)**: the existing `vllm-omni` container serves reasoning (and
  ideally action) in addition to generation, off the same resident quantized
  model. Fall back to **option (c)**: run reasoning/action as side-by-side
  backends the orchestrator swaps between. **Option (b)** — consolidating
  generation onto the `diffusers` engine — is excluded, because diffusers `t2v`
  quality is unacceptable (owner) and the proven `t2i` path is `vllm-omni`.
- Achieve **zero-BF16**: eliminate the BF16 base download from the default
  deployment. For action this requires bundling the action adapters into the
  quantized checkpoint (a checkpoint-repackaging task).
- Collapse three deploy postures into **two** (`fp8`, `nvfp4`), each all-modes by
  default: drop the reasoning overlay and the `WITH_REASONING` build split.
- Promote a mode to "GPU-verified" and default-on **only** after it runs end to
  end on the 5090 **and** the owner manually approves its output quality.
- Teach each mode by example: a lean README "See it in action" section linking a
  separate `docs/walkthrough.md` with per-mode example input → expected output
  and image placeholders the owner fills after verification.

This PRD and its companions are a **documentation-and-blueprint pass only**. They
define the sessions, contracts, and gates that later development sessions execute
one at a time. **No application code, configuration, `README.md`, or
`docs/walkthrough.md` content is written by this pass.**

## 3. Owner Decisions

Binding for this blueprint and the sessions it defines. Fixed with the owner
during the interview that produced this blueprint (2026-07-24). Feasibility of
the *technical* targets (D3/D4) is still gated by the `AM-S1` spike and the
owner's quality gate — an owner decision fixes *intent and constraint*, not
whether the hardware/kernels cooperate (`docs/evidence_map.md` rules).

1. **Phase identity.** Phase-5, tag `AM` ("All-Modes"). Sessions `AM-S1`..`AM-S6`,
   numbered fresh. Deliverables at `docs/` root. Gates `GATE-AM-S{n}-*`.
2. **Finish line = GPU-verified + default-on.** All three modes run end to end on
   the RTX 5090 and are enabled by default in both the `fp8` and `nvfp4` stacks.
   "Enable" means "works and is on by default", not "reachable but caveated".
3. **Zero-BF16 is a hard goal.** The default stacks serve all modes off the
   quantized-only checkpoint; the BF16 base download is eliminated from the
   default path. BF16 is **not** a silent fallback: any BF16 use is an explicit,
   documented owner decision recorded at a gate, never a shipped default.
4. **Serving strategy: (a) then (c); (b) excluded.** Try making `vllm-omni` serve
   reasoning and action first; fall back to side-by-side backends only where (a)
   is infeasible. Never consolidate generation onto `diffusers`.
5. **Do not regress `t2i`; never diffusers for `t2v`.** The `vllm-omni` `t2i`
   path (FP8 + NVFP4) stays GPU-verified end to end after every change. `t2v`/
   `i2v`/`t2v_audio` are served only by the quantized `vllm-omni` path. Diffusers
   is at most acceptable for `t2i`, never for `t2v`.
6. **Quality is judged by the owner, manually.** The owner launches the
   containers, runs custom example prompts, and rules on reasoning/action output
   quality. That verdict is the human decision gate that promotes a mode to
   "verified" and default-on.
7. **Vertical, FP8-first sequencing.** Prove the entire all-modes pipeline on FP8
   (the proven format) before extending to NVFP4 (the newer, riskier 4-bit
   Blackwell path).
8. **Docs last, two artifacts.** A lean README "See it in action" section links a
   separate `docs/walkthrough.md` (per-mode example input → expected output; image
   placeholders → `docs/images/…` filled by the owner post-verification). Written
   in the final session, after modes are verified, so no "expected output" or
   screenshot precedes a real run.
9. **This phase writes only `docs/**`.** No application code, configuration,
   `README.md`, or `docs/walkthrough.md` content is produced until a later session
   executes its contract.

## 4. Requirements

Requirement keywords follow RFC 2119. A claim not yet verified at blueprint time
is written as a verification task or session gate, not a shipped capability; a
speculative or spike-gated claim is never a MUST (`docs/evidence_map.md`).

### Functional

- **FR-1 (MUST)** `AM-S1` determines, by running on the RTX 5090 against the FP8
  quantized checkpoint, whether `vllm-omni` (`vllm serve --omni`) can serve
  **reasoning** (`/v1/chat/completions`) and whether it can serve **action** —
  and records a per-mode `(a)`-vs-`(c)` decision. It also confirms the action
  checkpoint gap (E-06) and decides whether bundling adapters via
  `tools/checkpoint_prep/` is the zero-BF16 action path. The spike's output is an
  owner-gated decision, not a shipped capability.
- **FR-2 (MUST)** `AM-S2` makes **reasoning** run end to end on the FP8 stack off
  the **quantized-only** checkpoint (no BF16 base, no reasoning overlay, no
  `WITH_REASONING` build), by the mechanism `AM-S1` selected. The `t2i` path is
  re-verified as non-regressed. Promotion to "verified" requires the owner's
  manual quality PASS (Decision 6).
- **FR-3 (MUST)** `AM-S3` makes **action** run end to end on the FP8 stack off a
  **quantized-only** checkpoint. Because the quantized checkpoint lacks action
  tensors (E-06), this MUST either bundle the bf16 `action_*` adapters into the
  quantized checkpoint (e.g. via `tools/checkpoint_prep/`, re-pinning a new
  revision and re-verifying `t2i` against it) or serve action by the `AM-S1`
  fallback — with any residual BF16 dependency surfaced as an explicit owner
  decision (INV-4). Promotion requires the owner's manual quality PASS.
- **FR-4 (MUST)** `AM-S4` simplifies the deploy surface so a plain `make up-fp8`
  brings up **all three modes** by default: remove the `docker-compose.reasoning.yml`
  overlay dependency and the `WITH_REASONING` build split from the default path;
  reconcile `Makefile` (drop/repoint `up-fp8-reasoning`), `.env.example`,
  `deploy/**`, and `docs/model_setup.md` so no BF16 base is required. A full
  all-modes smoke passes on FP8; `t2i` remains non-regressed.
- **FR-5 (MUST)** `AM-S5` extends the verified FP8 design to **NVFP4** and
  GPU-verifies all three modes on NVFP4, handling the newer 4-bit Blackwell
  kernel risk. Where a mode cannot be served on NVFP4 off quantized weights, the
  `(c)` fallback is attempted; a residual limitation is an explicit owner decision
  and is documented honestly (INV-7), not hidden.
- **FR-6 (MUST)** After `AM-S4`/`AM-S5`, a mode is **enabled by default** in a
  given stack only if it passed that stack's GPU gate and the owner's quality
  gate; a mode/format that did not pass is not silently enabled and not claimed
  verified (INV-6/INV-7).
- **FR-7 (MUST)** `AM-S6` adds a README "See it in action" section (per-mode
  example input → what to expect, in prose) and a separate `docs/walkthrough.md`
  (per-mode step-by-step with example input → expected output and image
  placeholders referencing `docs/images/…`). It updates the README per-mode
  verification status to reflect only what actually passed, and reconciles the
  BF16-license discrepancy (E-14) in `docs/model_setup.md`.
- **FR-8 (MUST)** Across all sessions, the residency safety net is preserved: a
  different-residency request preempts, VRAM stays within budget, and no plane is
  loaded while another is resident unless a co-residency/plane-merge is explicitly
  verified (INV-5). The public API request/response schemas do not change shape
  unless a session contract authorizes it (INV-8).
- **FR-9 (SHOULD)** `AM-S6` keeps the README a single lean file with the heavy
  visual walkthrough linked out to `docs/walkthrough.md`, consistent with the
  phase-4 ADHD posture; it does not inline screenshots into the README.

### Non-Functional

- **NFR-1 (MUST)** No secret, token, private host, private absolute path, model
  weight, or generated-media binary is committed as part of any session. Image
  placeholders in `docs/walkthrough.md` are markdown links to `docs/images/…`
  paths the owner populates; no image binary is added by the sessions.
- **NFR-2 (MUST)** Every release-affecting recommendation in
  `docs/project_contract.md` has an evidence row in `docs/evidence_map.md` or is
  marked speculative / spike-gated / owner-decision with a named verification
  gate. Speculative claims do not become MUST requirements.
- **NFR-3 (MUST)** Every session that changes a serving path re-verifies the
  `vllm-omni` `t2i` path (FP8 and, from `AM-S5`, NVFP4) end to end and records the
  standard GPU evidence fields; `t2i` non-regression is a blocking gate (INV-2).
- **NFR-4 (MUST)** Promotion of any mode to "GPU-verified" is backed by (i) a
  recorded end-to-end run on the RTX 5090 and (ii) the owner's recorded manual
  quality verdict; neither alone suffices (INV-6, Decision 6).
- **NFR-5 (MUST)** The reproducibility-from-public-inputs posture is preserved: if
  a session re-exports a checkpoint (action adapters), it pins a new immutable
  revision, records it in `docs/model_setup.md`, keeps weights external (never
  committed), and re-verifies `t2i` against the new revision (NFR-1, E-13).

## 5. Acceptance Criteria

This blueprint's scope is done only when all are true:

1. `docs/prd.md`, `docs/project_contract.md`, `docs/evidence_map.md`,
   `docs/risk_register.md`, and `docs/eval_seed_cases.md` exist at `docs/` root,
   and `docs/session_{1..6}.md` / `docs/session_{1..6}_contract.yaml` exist for
   `AM-S1`..`AM-S6`.
2. Each session document defines objective, in-scope, out-of-scope, deliverables,
   and exit criteria, and references the repository evidence it depends on.
3. Each session contract classifies risk, routes per the risk router, and fixes a
   blast radius (allowed/forbidden files), invariants, deterministic checks,
   GPU/owner gates where applicable, adversarial cases, and a done condition.
4. `docs/evidence_map.md` carries a row for every major recommendation, marks
   speculative/spike-gated/owner-decision claims (never promoting them to MUST),
   and states the BF16-license discrepancy with the chosen handling.
5. The contract pack survives a second, adversarial compilation pass: the
   zero-BF16-as-unbacked-MUST hazard, the action-tensor checkpoint gap, the
   option-(a)-serves-action assumption, the `t2i`-regression hazard, the
   diffusers-`t2v` exclusion, the verify-then-default ordering, the
   coresidency-assumption drift, and the docs-before-verification hazard are each
   resolved in the text rather than left latent.
6. No application code, configuration, `README.md`, `docs/walkthrough.md`, or
   non-`docs/` content is modified by this pass.

## 6. Non-Goals

- Writing or editing any application code, configuration, `README.md`,
  `docs/walkthrough.md`, or non-`docs/` content during this blueprint pass. This
  PRD and its companions define sessions; they do not execute them.
- WebUI feature work: the Studio/Reasoning/Action tabs already exist and are wired
  (E-12). A session touches WebUI only if its own verification surfaces a UI bug.
- Consolidating generation onto the `diffusers` engine, or using `diffusers` for
  `t2v`/`i2v`/`t2v_audio` (Decision 4/5).
- Changing the auth posture (still no application auth), the guardrails posture
  (still `--no-guardrails` by design, E-15), or network binding.
- Runtime FP8↔NVFP4 switching within one stack; each stack still serves exactly
  one quantized checkpoint (the only on-demand switching is Studio/Action ↔
  Reasoning residency).
- Editing `docs/archive/**`.
- Guaranteeing that zero-BF16 or option (a) is technically achievable for every
  mode/format at blueprint time; that is what `AM-S1` and the per-session gates
  determine.

## 7. Session Plan

Vertical, FP8-first (Decision 7). All enablement sessions are high risk
(model/data pipelines, dependency changes) and route with independent
verification + the owner's human decision gate (`docs/project_contract.md` §5).

| # | Session | Risk | Primary gate |
|---|---|---|---|
| AM-S1 | **Feasibility spike (FP8).** Can `vllm-omni` serve reasoning + action off the quantized-only transformer? Confirm the action-tensor gap; decide `(a)`-vs-`(c)` per mode and the zero-BF16 action packaging path. | high | `GATE-AM-S1-SPIKE` (owner decision) |
| AM-S2 | **Reasoning enabled + GPU-verified on FP8**, zero-BF16, by the `AM-S1` mechanism; `t2i` non-regressed. | high | `GATE-AM-S2-REASONING` (owner quality) |
| AM-S3 | **Action enabled + GPU-verified on FP8**, zero-BF16 (bundle action adapters into the quantized checkpoint, or the `AM-S1` fallback); `t2i` non-regressed. | high | `GATE-AM-S3-ACTION` (owner quality) |
| AM-S4 | **Orchestration simplification + default-on (FP8).** One `make up-fp8` = all three modes; drop the reasoning overlay + `WITH_REASONING`; reconcile `Makefile`/`.env.example`/`deploy/**`/`model_setup.md`; full all-modes smoke. | high | `GATE-AM-S4-ORCHESTRATION` (GPU smoke) |
| AM-S5 | **Extend + GPU-verify on NVFP4** (4-bit Blackwell kernels; `(c)` fallback per mode as needed); default-on for modes that pass. | high | `GATE-AM-S5-NVFP4` (owner quality) |
| AM-S6 | **README "See it in action" + `docs/walkthrough.md`** (per-mode example → expected output, image placeholders); reconcile per-mode status + BF16 license. | low | `GATE-AM-S6-DOCS` (honesty + link checks) |

The exact count is settled here but may adapt in execution: `AM-S1` may fold into
`AM-S2` if the spike is cheap and conclusive; `AM-S5` may split by mode if NVFP4
proves a harder lift per mode. Any such change is recorded, with rationale, in the
affected session docs — not applied silently.
