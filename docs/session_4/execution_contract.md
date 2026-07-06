# Session 4 Execution Contract - Hugging Face Checkpoint Verification and Model Setup Docs

Session: MIG-S4
Risk: high · Routing: branch_and_compare · Gate: `GATE-MIG-S4-HF`

## Planned file changes

Created:
- `docs/session_4/brainstorming.md`, `proposal.md`, `design.md`,
  `specs/{hf_checkpoint_verification,checkpoint_layout_compatibility,public_model_setup_contract,checkpoint_drift_disposition}.md`,
  `tasks.md`, `plan.md`, `execution_contract.md`
- `docs/session_4/probes/verify_hf_checkpoints.py`, `probes/evidence.json`, `probes/summary.md`
- `docs/session_4/hf_verification.md`, `drift_report.md`
- `docs/session_4/failure_arbiter.md` (only if a failure is classified),
  `sharded_review.md`, `adversarial_verification.md`
- `docs/model_setup.md`
- `docs/eval_corpus/mig_s4_*.md`

Updated:
- `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
  `docs/handoff.md`

## Allowed blast radius

Permitted: `docs/session_4/**`, `docs/model_setup.md`, `docs/evidence_map.md`,
`docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/eval_corpus/**`.

Forbidden (stop if a change seems required): any model weight/media file, Dockerfiles
and Compose files, `README.md`, `.github/**`, and all source/schema/test/tool code
(`api/**`, `webui/**`, `schemas/**`, `tests/**`, `tools/**`, `pyproject.toml`,
`uv.lock`). The probe under `docs/session_4/probes/` is docs-scoped evidence tooling,
not runtime code, and imports (does not modify) `tools/checkpoint_prep/safetensors_io.py`.

## First test to write

The probe's `--check` self-test (pure-core, spec-derived), written before the network
shell. Minimum first assertions (from `specs/checkpoint_layout_compatibility.md`):

```python
assert precision_from_header_keys({"blk.weight_quantizer._double_scale": {}}) is Precision.NVFP4
assert precision_from_header_keys({"blk.weight_quantizer._scale": {}}) is Precision.FP8
```
`python3 docs/session_4/probes/verify_hf_checkpoints.py --check` must fail before the
functions exist, then pass once implemented.

## Checks to run after each task

- Deterministic (contract): `git ls-remote` FP8 + NVFP4 `HEAD 'refs/heads/*'`;
  `python3 -c "import huggingface_hub; print(huggingface_hub.__version__)"`;
  `rg -n "wfen/Cosmos3-Nano-(FP8|NVFP4)-Blockwise" docs`.
- Probe: `python3 docs/session_4/probes/verify_hf_checkpoints.py --check` (spec assertions).
- Provenance regression over the session's own output (R-01 / S3 eval seed):
  `rg -n -i -e '-wfen' -e 'Blockwise-dist' -e 'Blockwise-local' -e 'NVFP4-AWQ' -e '/data/home' -e '/home/[a-z]' -e 'intranet' -e 'hf_[A-Za-z0-9]{20}' -e 'sk-[A-Za-z0-9]{20}' docs/session_4/ docs/model_setup.md`
  → must return no match before each commit.
- Torch-free guard: probe imports neither `torch` nor `diffusers`.

## Review axes to run at the end

correctness · security · tests · architecture · performance (per
`docs/agent_workflow/prompts/sharded_review.md`). Each reviewer read-only; reports
severity + evidence + violated clause + smallest safe fix + confidence. Fix only
High/Critical; re-run the checks after fixes.

## Adversarial verifier brief

Fresh context; sees only `docs/session_4_contract.yaml`, the session diff, and the
evidence bundle — not this conversation. Task: falsify "GATE-MIG-S4-HF passes with
public checkpoint setup ready for Docker and README." Specifically attempt to show:
(a) a revision or license is unrecorded or inconsistent between sources; (b) a claimed
layout/self-containment fact is not backed by `evidence.json`; (c) a local header
finding is asserted for the public artifact without a `local==public` SHA match;
(d) a drift lacks an owner disposition or routed risk row; (e) a dev-only variant name,
host path, or secret leaked into any session doc; (f) `model_setup.md` treats model
weights as MIT or claims an unbacked mode is verified. Any confirmed item fails the
session and is routed through the Failure Arbiter.

## Concrete done condition

`GATE-MIG-S4-HF` is satisfied when all hold, each backed by `evidence.json`:
1. FP8 and NVFP4 revisions recorded (40-hex, `ls-remote` == `HfApi.sha`).
2. Model license (`openmdw-1.0`) recorded per repo and separated from repo MIT in
   `docs/model_setup.md`.
3. Full public file layout + self-containment documented against loader expectations,
   with local header findings gated by `local==public` SHA.
4. Every drift (D1–D4) has a severity, an owner disposition, and a routed risk row.
5. `docs/model_setup.md` delivers repo IDs+revisions, `COSMOS3_*` env vars, mount
   layout, license separation, and a per-mode compatibility matrix (reasoning +
   action/forward_dynamics marked beta-limited).
6. Deterministic checks + probe `--check` + provenance regression all clean.
7. Sharded review has no unresolved High/Critical; adversarial verifier passes.
8. `docs/handoff.md` hands S6/S7 the revisions, license notes, env vars, mount layout,
   and drift report.
