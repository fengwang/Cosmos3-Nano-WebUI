# Session 4 Brainstorming - Hugging Face Checkpoint Verification and Model Setup Docs

Date: 2026-07-06
Session: MIG-S4
Status: Approved design (owner approved on 2026-07-06)

## Context Explored

- Read `docs/prd.md`, `docs/project_contract.md`, `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/session_4.md`, `docs/session_4_contract.yaml`,
  and the Session 3 `docs/handoff.md`.
- Mapped the imported runtime's checkpoint assumptions (read-only) across
  `api/engines/{diffusers_oracle,diffusers_action,vllm,vllm_omni}` and
  `tools/checkpoint_prep/**`.
- Ran the session contract's deterministic checks against the live public
  Hugging Face repos and the local checkpoints available on the build host.

## Baseline Checks (ran during startup)

- Both public HF repos are reachable and pinned:
  - `wfen/Cosmos3-Nano-FP8-Blockwise` HEAD/`main` = `4e181f996abf03f3425298ef692e6e5e56fd46a4`.
  - `wfen/Cosmos3-Nano-NVFP4-Blockwise` HEAD = `b5c9332efbaefa72c99890b1b1150da12ca9256c`.
- `HfApi().model_info(...)` returns `card_data.license == openmdw-1.0` for both.
- `huggingface_hub` `1.21.0` is importable; `curl -I` to both model pages returns HTTP 200.
- The FP8, NVFP4, and BF16-base checkpoints are present on the build host under the
  documented `/data/models/<repo-name>` mount convention, so torch-free
  header-level probes are feasible without any download in CI.

## Key Findings That Shaped The Design

1. **The verification is executable, not aspirational.** Because both HF network
   and local checkpoints are reachable, this session can record *real* revisions,
   license metadata, public file manifests, blob sizes/LFS SHAs, and safetensors
   header contents — rather than writing a harness for the owner to run later.
2. **Runtime layout expectations are concrete and testable.**
   `diffusers_oracle.loader.discover_transformer_dir` requires a transformer dir
   containing `*.safetensors` + `modelopt_state.pt` + `config.json` (tries a nested
   `transformer/transformer/` first, then flat `transformer/`); precision is read
   from `<root>/quantization_config.json` (`recipe` field) and confirmed by observing
   `weight_quantizer._double_scale` (NVFP4) vs its absence (FP8). These are the exact
   assertions the public artifacts must satisfy.
3. **The public checkpoints are self-contained for the generation path.** Both repos
   ship `transformer/`, `vae/`, `text_tokenizer/`, `vision_encoder/`, `sound_tokenizer/`,
   `scheduler/`, `model_index.json`, `config.json`, and `generation_config.json` — the
   layout the diffusers oracle/action engines expect.
4. **NVFP4 is asymmetric to FP8 (potential drift).** The public FP8 repo lists a
   top-level `quantization_config.json` (and `quantizer_map_diff.json`, plus
   `transformer/modelopt_state.pt` and shipped loader scripts `load_checkpoint.py` /
   `load_quantized.py`). The public NVFP4 repo's file listing does **not** show these.
   The oracle loader reads `quantization_config.json` and requires `modelopt_state.pt`,
   so the NVFP4 artifact must be probed precisely to confirm whether the loader path
   still resolves (observe-precision fallback) or whether this is load-blocking drift.
5. **The BF16 base model is not public.** `wfen/Cosmos3-Nano` returns
   "Repository not found". The reasoner (`COSMOS3_REASONER_MODEL_DIR`) and the
   action/forward_dynamics graft (`COSMOS3_BASE_ACTION_DIR`) both reference a BF16
   base checkpoint. The two published repos back the *generation* modes; reasoning
   and action are not publicly backed and must be marked beta-limited.
6. **External-artifact hygiene concern.** The public FP8 repo contains files with
   dev-process-looking names (e.g., `_s2_*.md`). Their existence is public, but their
   contents are not cited here; the owner should review/remove them out-of-band.
7. **Provenance risk is the dominant guardrail.** The build host holds co-located
   dev-only checkpoint variants (unpublished). Per R-01 and the Session 3 eval seed,
   public docs cite only the public repo IDs + revisions and use `/path/to/<Repo>` or
   the `/data/models/<Repo>` mount convention — never dev-only variant directory names
   or absolute host paths — and the private-value regression runs over this session's
   own `docs/session_4/**` before every commit.

## Clarifying Questions And Answers

| # | Question | Decision |
|---|---|---|
| Q_A | How rigorous should verification be, given local + network access? | **HF metadata + local header-level probes**, cross-checked against public LFS SHAs so evidence describes the *public* artifact; commit a torch-free, re-runnable probe under `docs/session_4/probes/`. No torch/GPU load. |
| Q_B | The BF16 base for reasoning + action/forward_dynamics is not public. How to handle the full surface? | **Mark unbacked modes beta-limited** via a per-mode compatibility matrix; open a risk row; hand the gap to S6/S7/S8. No stop-the-line (aligns INV-8, R-08). |
| Q_C | What should `docs/model_setup.md` be, given S7 owns README and S6 owns Docker? | **Authoritative model-setup contract + minimal operator notes**: repo IDs/revisions, `COSMOS3_*` env table, mount layout, self-containment, license separation, per-mode matrix, drift caveats. Polished prose deferred to S7. |
| Q_D | Empty NVFP4 model card (R-04)? | Document the gap + recommend a follow-up; **do not** draft/push HF model-card content (HF write is out of scope for this repo). |
| Q_E | Commit behavior? | **Commit locally at clean checkpoints on `session-4`, no push** (mirrors S3 Q_D). |

## Approaches Considered

### Approach A (chosen): Executable probe as evidence source + human-authored analysis
A small torch-free probe under `docs/session_4/probes/` gathers machine facts —
revisions (`git ls-remote` / `HfApi`), the full public file manifest + sizes + LFS
SHAs (`list_repo_files` / `get_paths_info`), and local safetensors-header +
quant-config parses (reusing the tested `tools/checkpoint_prep/safetensors_io.py:parse_header`)
— then emits a JSON evidence bundle + human summary. The verification note, drift
report, and `model_setup.md` are authored from that bundle.
- Pros: reproducible; strongest evidence for a HIGH branch-and-compare gate; reuses
  proven code; ACD-clean (pure parse/derive/compare vs isolated network/FS actions);
  centralizes provenance scrubbing at the reporting boundary.
- Cons: more up-front effort than pasting command output.

### Approach B (rejected): Ad-hoc commands + transcribed evidence
Run the contract commands by hand and paste outputs into the note.
- Rejected: not re-runnable; weak for a HIGH-risk gate; higher transcription and
  provenance-leak risk.

### Approach C (rejected): Full loader-exercising verification (torch/diffusers load)
Actually import diffusers/torch and attempt a real checkpoint load.
- Rejected: pulls torch/diffusers/GPU into a docs-only session; out of scope
  (GPU is the `MIG-S8` gate); blast radius forbids code changes. Header-level probes
  answer the layout/compatibility question without a load.

## Validated Design (Summary)

**Verification method (A)**
- Evidence sources: (i) HF network — revisions, `card_data.license`, model-card
  state, full public file manifest, sizes, LFS SHAs; (ii) local `/data/models/<Repo>`
  — safetensors headers + `config.json` / `quantization_config.json`, cross-checked
  against public SHAs/sizes to confirm `local == public` before trusting local internals.
- Probe is torch-free/numpy-free, committed under `docs/session_4/probes/`, re-runnable,
  and emits `evidence.json` + a summary. Network- and FS-touching steps are isolated
  actions; parsing/derivation/comparison are pure calculations.

**Deliverables (all documentation)**
- `docs/session_4/hf_verification.md` — repo IDs + pinned revisions, license + card
  state per repo, full public layout, self-containment analysis, header/quant-config
  probe results, `local == public` cross-check, evidence citations.
- `docs/model_setup.md` — authoritative contract: repo IDs + revisions, `COSMOS3_*`
  env-var table, mount layout, self-containment facts, license separation
  (`openmdw-1.0` model vs MIT repo), per-mode compatibility matrix (generation backed;
  reasoning + action/forward_dynamics beta-limited), drift caveats, minimal operator notes.
- `docs/session_4/drift_report.md` — D1 NVFP4↔FP8 metadata asymmetry + loader-compat
  analysis; D2 non-public BF16 base → reasoning/action beta-limited; D3 dev-scratch +
  asymmetric loader scripts in the public FP8 repo (external hygiene); D4 NVFP4
  empty/placeholder card. Each with owner disposition + routed risk row.
- Updates: `docs/evidence_map.md`, `docs/risk_register.md` (R-03/R-04 + D1/D3),
  `docs/eval_seed_cases.md` + `docs/eval_corpus/` (EV-MIG-HF-FP8-METADATA,
  EV-MIG-HF-NVFP4-METADATA).
- Refining pack + loop artifacts under `docs/session_4/`.

**Capabilities (spec files)**
- `hf_checkpoint_verification` — reachability, revision pinning, license/card capture,
  public file manifest.
- `checkpoint_layout_compatibility` — layout + quant metadata vs loader expectations,
  including the FP8/NVFP4 asymmetry.
- `public_model_setup_contract` — env vars, mounts, per-mode matrix, license separation.
- `checkpoint_drift_disposition` — drift capture + routing + risk rows.

**Guardrails (R-01)**
- Cite only public repo IDs + revisions; use `/path/to/<Repo>` or `/data/models/<Repo>`;
  never name dev-only variants or host paths; run the private-value regression over
  `docs/session_4/**` before every commit.

**Blast radius**
- Only `docs/session_4/**`, `docs/model_setup.md`, `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/eval_corpus/**`.
  No code / schema / Docker / README / `.github` edits. The probe lives under
  `docs/session_4/probes/` (within blast radius).

**Checks / review / done**
- After each task: contract deterministic checks + probe assertions + private-value
  regression over `docs/session_4/**`. HIGH risk → 5-axis sharded review + fresh-context
  adversarial verifier. Done = `GATE-MIG-S4-HF`: revisions recorded, license captured,
  layout + runtime assumptions documented, every drift dispositioned, handoff vars
  delivered to S6/S7.

**Persistence**
- Commit locally at clean checkpoints on `session-4`. Do not push.

## Owner-Approved Judgment Calls (defaulted, not blocking)
- Commit locally at checkpoints on `session-4`, no push (Q_E).
- Document the empty NVFP4 card and recommend a follow-up; do not draft/push HF
  model-card content (Q_D).
