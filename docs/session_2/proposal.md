# Session 2 Proposal - vLLM-Omni Patch Rebase And Public Pin

Date: 2026-07-06
Session: MIG-S2
Status: Derived from approved brainstorming

## Motivation

Cosmos3-Nano-WebUI cannot depend on a private vLLM-Omni checkout or unpublished
patch. The public beta needs a public GitHub fork commit or tag containing the
Cosmos3 quantized-checkpoint patch line, plus deterministic evidence that the
patch was rebased and checked against the current fork base.

## Agreed Changes

- Use `vllm-omni` as the public fork checkout.
- Use the owner-authorized local historical checkout and eight-commit range as
  the patch source, without recording private source path, branch, or source
  hashes in public docs.
- Preserve the 8 patch commits while replaying them onto public fork `origin/main`
  at `d4a869fe5e2edd49af48026051948c8d1018d727`.
- Resolve conflicts only in Cosmos3, checkpoint adapter, quantization, and
  matching test surfaces.
- Use `vllm-omni/.venv-mig-s2` for targeted deterministic
  tests.
- Publish public branch `mig-s2-cosmos3-quant-pin` and tag
  `cosmos3-nano-webui-mig-s2`.
- Record the final commit/tag, install command, conflict notes, checks, failure
  classifications, and handoff guidance.

## Capabilities

### New Capabilities

1. **Public Fork Patch Pin**
   - A public branch and immutable tag in `git@github.com:fengwang/vllm-omni.git`
     contain the selected Cosmos3 patch line.

2. **ModelOpt Checkpoint Adapter Support**
   - vLLM-Omni can load public Cosmos3 ModelOpt-native FP8 blockwise, FP8 W8A16,
     and NVFP4 checkpoint layouts through explicit checkpoint adapters.

3. **Cosmos3 Quantization Runtime Guards**
   - Cosmos3 quantized runtime paths expose explicit FP8 W8A16 and NVFP4
     configuration/guard behavior without requiring model weights in deterministic
     tests.

4. **Session Evidence And Handoff**
   - The WebUI repo records public pin evidence, install instructions, known
     limitations, and next-session warnings.

### Modified Capabilities

1. **vLLM-Omni Deterministic Test Gate**
   - The Session 2 deterministic checks are interpreted against the external fork
     checkout, not the WebUI seed repo. Stale or moved test paths must be resolved
     by explicit failure classification and documented replacement paths.

## Impact

Affected external fork areas:

- `vllm_omni/diffusion/model_loader/checkpoint_adapters/**`
- `vllm_omni/diffusion/model_loader/diffusers_loader.py`
- `vllm_omni/diffusion/models/cosmos3/**`
- `vllm_omni/quantization/**`
- `tests/diffusion/model_loader/**`
- `tests/diffusion/models/cosmos3/**`
- `tests/diffusion/quantization/**`
- `tests/model_executor/quantization/**` only if preserving upstream test
  taxonomy is required by the patch source.

Affected WebUI repo areas:

- `docs/session_2/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/handoff.md` as required by the user lifecycle.
- `docs/eval_corpus/**` only if a caught or missed issue needs an eval seed.

No WebUI runtime source, model weights, Docker publishing workflows, or GitHub
secrets are in scope.
