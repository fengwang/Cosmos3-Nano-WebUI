# Session 4 Proposal - Hugging Face Checkpoint Verification and Model Setup Docs

Date: 2026-07-06
Session: MIG-S4
Status: Derived from approved brainstorming

## Motivation

The public beta serves external weights from two Hugging Face repos
(`wfen/Cosmos3-Nano-FP8-Blockwise`, `wfen/Cosmos3-Nano-NVFP4-Blockwise`). Docker
(S6), README (S7), and the release gate (S8) will make setup and compatibility
claims about those artifacts, but no public evidence yet ties the *public*
checkpoints to the runtime's loader expectations. Session 3 imported the loaders
(`api/engines/diffusers_{oracle,action}`, `api/engines/vllm`) with concrete,
testable layout and quantization-metadata assumptions; those assumptions have never
been checked against what a user actually downloads from Hugging Face.

Session 4 produces that evidence and the public model-setup contract. Because both
the HF network and the local checkpoints are reachable from the build host, the
verification is executable: real revisions, license metadata, public file
manifests, blob sizes/LFS SHAs, and safetensors headers are recorded, cross-checked
so the evidence describes the *public* artifact, and turned into an authoritative
setup contract plus a drift report. This session writes documentation only; it
does not change code, schemas, Docker, README, or `.github`.

## Agreed Changes

- Verify via **Approach A**: an executable, torch-free probe under
  `docs/session_4/probes/` that records revisions, license/card state, the full
  public file manifest + sizes + LFS SHAs, and local safetensors-header /
  quant-config parses (reusing `tools/checkpoint_prep/safetensors_io.py:parse_header`).
  Cross-check local files against public LFS SHAs so evidence is about the *public*
  artifact. No torch/GPU load.
- Record both HF revisions (FP8 `4e181f99…`, NVFP4 `b5c9332e…`) and the model
  license (`openmdw-1.0`), kept separate from the repo's MIT code license.
- Document the full public file layout and confirm/deny self-containment against
  the diffusers oracle/action loader expectations (`discover_transformer_dir`,
  `quantization_config.json` precision detection, required sidecars).
- Capture the FP8↔NVFP4 metadata asymmetry precisely and analyze loader
  compatibility for the NVFP4 artifact.
- Mark modes whose weights are not publicly backed (reasoning, action/forward_dynamics
  — they need a BF16 base repo that returns "not found") as **beta-limited** in a
  per-mode compatibility matrix, and route the gap to S6/S7/S8.
- Write `docs/model_setup.md` as the authoritative model-setup contract: repo IDs +
  revisions, `COSMOS3_*` env-var table, mount layout, self-containment facts, license
  separation, per-mode matrix, drift caveats, and minimal operator notes. Polished
  prose and quickstart are deferred to S7; Docker/Compose wiring is deferred to S6.
- Record all drift with owner dispositions in `docs/session_4/drift_report.md` and
  open/update risk rows.
- Guardrail (R-01): cite only public repo IDs + revisions; use `/path/to/<Repo>` or
  the `/data/models/<Repo>` mount convention; never name dev-only checkpoint variants
  or host paths; run the private-value regression over `docs/session_4/**` before
  every commit.
- Commit refining docs + evidence at clean checkpoints on `session-4`; do not push.

## Capabilities

### New Capabilities

1. **HF Checkpoint Verification** (`hf_checkpoint_verification`)
   - The public FP8 and NVFP4 HF repos are proven reachable, their revisions are
     pinned, their model license and model-card state are recorded, and their full
     public file manifest (with sizes and LFS SHAs) is captured — using public
     network evidence, reproducibly.

2. **Checkpoint Layout Compatibility** (`checkpoint_layout_compatibility`)
   - The public artifact layout and quantization metadata are checked against the
     imported loaders' concrete expectations (transformer dir discovery, required
     sidecars, precision detection). Header-level probes run on local files that are
     first confirmed byte-identical to the public artifact via LFS SHA cross-check.
     The FP8↔NVFP4 asymmetry is characterized and its loader impact analyzed.

3. **Public Model Setup Contract** (`public_model_setup_contract`)
   - `docs/model_setup.md` authoritatively defines, for S6/S7 to consume: public
     repo IDs + pinned revisions, `COSMOS3_*` environment variables, mount layout,
     self-containment facts, license separation (model `openmdw-1.0` vs repo MIT),
     and a per-mode compatibility matrix that marks publicly-unbacked modes
     beta-limited.

4. **Checkpoint Drift Disposition** (`checkpoint_drift_disposition`)
   - Every mismatch between the public artifacts and runtime assumptions (NVFP4↔FP8
     metadata asymmetry, non-public BF16 base, external-repo hygiene, empty NVFP4
     card) is captured with an explicit owner disposition and a routed risk row
     before Docker or README depends on it.

### Modified Capabilities

None. Session 4 introduces verification and setup documentation; it does not modify
a previously shipped WebUI-repo capability, and it changes no code, schema, or
public API surface (blast radius is documentation only).

## Impact

Affected public docs (created/updated):

- `docs/session_4/**` (this refining pack + `hf_verification.md` + `drift_report.md`
  + `probes/**` + loop artifacts `failure_arbiter.md`, `sharded_review.md`,
  `adversarial_verification.md`)
- `docs/model_setup.md` (new authoritative setup contract)
- `docs/evidence_map.md`, `docs/risk_register.md` (R-03/R-04 + drift rows)
- `docs/eval_seed_cases.md` and `docs/eval_corpus/**` (EV-MIG-HF-FP8-METADATA,
  EV-MIG-HF-NVFP4-METADATA, plus any caught/missed seed)
- `docs/handoff.md` (Session End Protocol)

Affected code / APIs / systems: none. No source, schema, Docker, README, or
`.github` file is edited. The probe under `docs/session_4/probes/` is evidence
tooling within the docs blast radius, not runtime code, and is torch-free.

Dependency impact: none added to the project. The probe uses `huggingface_hub`
(already present, `1.21.0`) and the standard library only; it reuses the imported
`tools/checkpoint_prep/safetensors_io.py` parser for header decoding.

Handoff impact: S6 (Docker), S7 (README/hygiene), and S8 (release gate) consume the
model-setup contract — repo revisions, license notes, `COSMOS3_*` env vars, mount
layout, and the drift report — as their public source of truth for checkpoints.
