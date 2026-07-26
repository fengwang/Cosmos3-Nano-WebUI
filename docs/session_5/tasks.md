# AM-S5 Tasks

Dependency-ordered. Each task is verifiable. Specs: `specs/nvfp4-reasoner-serving.md`,
`specs/nvfp4-all-modes-wiring.md`. Design: `design.md`. Probes done (`evidence/P1`–`P2`) — all three
NVFP4 modes technically pass; implementation is the wiring for the proven modes.

## 1. NVFP4 reasoner image + vLLM patch (port the GPU-proven prototype)
- [ ] 1.1 Add `deploy/vllm-reasoner/patch-nvfp4/nvfp4_blockwise_w4a16_vllm.py` (from `evidence/fork_prototype_nvfp4/`).
- [ ] 1.2 Add `deploy/vllm-reasoner/patch-nvfp4/cosmos3.py` (NVFP4 sidecar map).
- [ ] 1.3 Add `deploy/vllm-reasoner/patch-nvfp4/quantization__init__.py` (stock omni `__init__` + nvfp4 registration).
- [ ] 1.4 Add `deploy/vllm-reasoner-nvfp4.Dockerfile` (mirror `vllm-reasoner.Dockerfile`; COPY the 3 nvfp4 patch files; CMD `--quantization nvfp4_blockwise_w4a16`, no `--omni`, no offload).

## 2. NVFP4 compose wiring
- [ ] 2.1 Add a `vllm-reasoner` service to `deploy/docker-compose.nvfp4.yml` (build the nvfp4 Dockerfile; same fixed container name/port shape as FP8; NVFP4 checkpoint mount; `--quantization nvfp4_blockwise_w4a16 --max-model-len 8192 --gpu-memory-utilization 0.85`; no offload).
- [ ] 2.2 Add the api reasoner caps to the nvfp4 `api` env (`COSMOS3_REASONER_MAX_CONTEXT=7680`, `COSMOS3_REASONER_MAX_OUTPUT=7680`).

## 3. Bring-up
- [ ] 3.1 `Makefile up-nvfp4`: `stop vllm-omni vllm-reasoner` (add the reasoner to the guard-stop).

## 4. Env doc
- [ ] 4.1 `.env.example`: NVFP4 all-modes note (still zero-BF16; the reasoner reuses the NVFP4 checkpoint).

## 5. Tests (spec-derived, deterministic)
- [ ] 5.1 `tests/deploy/test_nvfp4_allmodes_wiring.py`: nvfp4 config renders a `vllm-reasoner` with `nvfp4_blockwise_w4a16`, only the NVFP4 checkpoint mount, no BF16; omni has NO `--enable-layerwise-offload`.
- [ ] 5.2 Extend `tests/deploy/test_reasoner_context_cap_fits_model_len.py` to assert the nvfp4 stack's caps ≤ `--max-model-len` − headroom.
- [ ] 5.3 `test_up_nvfp4_stops_reasoner` (Makefile `up-nvfp4` stops both heavy planes).
- [ ] 5.4 FP8 non-regression render assertion (both stacks render; `git diff --exit-code deploy/docker-compose.fp8.yml`).

## 6. Docs / evidence / risk / eval / handoff
- [ ] 6.1 `docs/model_setup.md`: NVFP4 reasoning row → GPU-verified pending owner gate; NVFP4 reasoner note; NVFP4-assets conditioning-gap note.
- [ ] 6.2 `docs/evidence_map.md`: AM-S5 execution audit; S-B/S-D resolution; the fused-scale note.
- [ ] 6.3 `docs/risk_register.md`: R-03/R-04 → per-mode NVFP4 outcome.
- [ ] 6.4 `docs/eval_seed_cases.md`: NVFP4 seeds (circular-import guard, both-stack render, fused-scale quality watch).
- [ ] 6.5 `docs/handoff.md`: per-mode/per-format matrix; owner NVFP4 quality gate pending; the assets-gap decision.

## 7. Gate
- [ ] 7.1 Full CPU suite + both-stack `config` + `git diff schemas/openapi.json` green.
- [ ] 7.2 Sharded review (risk high) → fix High/Critical → adversarial verifier.
- [ ] 7.3 Stage the per-mode NVFP4 matrix for the owner's manual quality gate (INV-6).
