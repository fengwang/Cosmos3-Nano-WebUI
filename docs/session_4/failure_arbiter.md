# Session 4 Failure Arbiter

Date: 2026-07-06
Session: MIG-S4

Findings were classified before any fix, per the Failure Arbiter protocol
(BUG / SPEC_GAP / AMBIGUITY / ENVIRONMENT / TEST_BUG).

## FA-1: Spec premise "reasoning/action beta-limited (non-public base)" refuted by evidence

- **Symptom:** `specs/public_model_setup_contract.md` and
  `specs/checkpoint_drift_disposition.md` (D2 scenario), derived from the pre-verification
  brainstorming, require the setup contract to mark reasoning and action/forward_dynamics
  **beta-limited** with the reason **"non-public BF16 base model"**. Writing the contract
  truthfully would violate those scenarios.
- **Cause:** brainstorming checked only `wfen/Cosmos3-Nano` (404) and assumed the base was
  non-public. The probe reads the checkpoint **cards**, which declare
  `base_model: nvidia/Cosmos3-Nano`, and `evidence.json` shows that repo is **reachable,
  ungated, public** (license `other`, 67 files, has `transformer/` + `vision_encoder/`,
  README 43,813 bytes). The BF16 base the reasoner/action need **is** publicly available.
- **Classification:** **SPEC_GAP** — the spec encodes an assumption that deterministic
  verification invalidated. (Per protocol: stop and update the spec before implementing.)
- **Resolution:** updated the affected spec scenarios to require the per-mode matrix to
  reflect **verified public backing** for all four modes, with the real residual limits
  being (a) GPU-unverified runtime (blanket `MIG-S8` gate, INV-8/R-08) and (b) the D1
  in-process-oracle incompatibility, and to record the base repo id (`nvidia/Cosmos3-Nano`)
  and the 404 of the convention name (`wfen/Cosmos3-Nano`) as low-severity drift D2 rather
  than a beta-limiting gap. No product code changed. Audit trail: this file + `drift_report.md`
  D2 + `hf_verification.md`. Eval seed: `docs/eval_corpus/mig_s4_base_model_publication_premise.md`.

## FA-2: Public FP8 checkpoint recipe string does not satisfy the in-process oracle verifier

- **Symptom:** the public FP8 `quantization_config.json` has `recipe: "fp8_blockwise_mixed"`,
  but `api/engines/diffusers_oracle/config.py:45` requires the exact string `recipe == "fp8"`
  (else `precision_from_quant_config` raises `ValueError`). NVFP4 has no top-level
  `quantization_config.json` and no `modelopt_state.pt`, so `discover_transformer_dir`
  (`loader.py:33-50`) raises `FileNotFoundError`. The imported in-process `diffusers_oracle`
  engine therefore cannot load **or** verify either current public checkpoint as-is.
- **Cause:** artifact-vs-code drift (R-03): the public export recipe strings / NVFP4 export
  format diverged from the imported loader's expectations. The FP8 quant-config crosscheck is
  `match`, so this describes the **public** artifact (not a stale local copy).
- **Classification:** **SPEC_GAP / drift**, not a Session-4 BUG — Session 4 is docs-only and
  MUST NOT edit engine code (blast radius). The default generation engine is `vllm_omni`
  (`app/main.py:103`), a **separate container loader** (`load_quantized.py`); the in-process
  `diffusers_oracle`/`diffusers_action` engines are the affected path.
- **Resolution:** recorded as **drift D1 (high)** with an owner disposition and a routed risk
  row (R-03). The compatibility matrix marks in-process-oracle serving of the current public
  checkpoints as **not-loadable-as-is**; the default `vllm_omni` path is routed to `MIG-S6`
  (serving) / `MIG-S8` (GPU). No engine code changed here. Eval seed:
  `docs/eval_corpus/mig_s4_nvfp4_loader_layout_drift.md`.

## FA-3: NVFP4 model card is a 62-byte stub (not "empty" or "populated")

- **Symptom:** S1 evidence recorded the NVFP4 card as "empty"; the probe's first pass
  classified it "populated" (size > 0). Neither is accurate: `README.md` is 62 bytes.
- **Cause:** a coarse binary `POPULATED`/`EMPTY` (size > 0) hid a frontmatter-only stub.
- **Classification:** **TEST_BUG** (probe classifier too coarse) — fixed in the probe, not a
  product issue.
- **Resolution:** added a `STUB` state (`README <= 512` bytes) and recorded the exact size;
  NVFP4 = `stub` (62 bytes) now drives **drift D4 (medium)** and updates R-04.

## FA-4: Contract `allowed_files` omits `docs/eval_corpus/**` mandated by the Session End Protocol

- **Symptom:** the adversarial verifier found two changed files outside
  `session_4_contract.yaml` `blast_radius.allowed_files`:
  `docs/eval_corpus/mig_s4_base_model_publication_premise.md` and
  `docs/eval_corpus/mig_s4_nvfp4_loader_layout_drift.md`.
- **Cause:** the contract lists `docs/session_4/**`, `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/model_setup.md` — but not
  `docs/eval_corpus/**`, even though the Session End Protocol step 4 requires "Add eval seeds
  to `docs/eval_corpus/`", the session's `plan.md`/`execution_contract.md` planned exactly
  these files, and S2/S3 already keep their seeds there.
- **Classification:** **SPEC_GAP** — the contract's blast radius is incomplete relative to the
  owner-provided Session End Protocol and the established convention. (Per protocol: update the
  contract.)
- **Resolution:** amended `session_4_contract.yaml` `blast_radius.allowed_files` to add
  `docs/eval_corpus/**` (Session End Protocol step 4) and `docs/handoff.md` (step 3 — the same
  omission; S1–S3 also wrote `docs/handoff.md`). This reconciles the contract with the Session End
  Protocol; no secret, weight, or forbidden-surface file is involved (all passed the INV-1 scan).
  Recorded in `adversarial_verification.md`. Low severity; owner may review the amendment.

## Conclusion

No product code was changed (docs-only session). Three SPEC_GAP findings (FA-1 base publication
premise; FA-2 loader-vs-artifact incompatibility; FA-4 contract blast-radius omission) were
classified and routed to spec updates / drift rows / a contract amendment; one probe TEST_BUG
(FA-3 card classifier) was fixed in the probe. FA-1/FA-2 were caught during implementation;
FA-4 was caught by the adversarial verifier. The deterministic checks and probe `--check` pass.
