# AM-S5 Adversarial Verification

Date: 2026-07-26 · Fresh-context verifier (subagent), read-only, saw only `session_5_contract.yaml` + the
diff + `docs/session_5/evidence/**` + `execution_contract.md`. Task: falsify `GATE-AM-S5-NVFP4`.

## VERDICT: PASS — the technical done condition could not be falsified.

The verifier independently re-ran the deterministic gates (did not trust the audit prose) and attempted
to break each clause. Findings: **none of Critical/High/Medium.** Owner quality gate correctly PENDING
(no over-claim).

## What it independently verified
- **CPU suite** `uv run pytest -m "not gpu"` → exit 0, **572 tests, zero skips/xfail/errors** (no skips
  masking failures).
- **Forbidden files** — `git diff --stat` scrutinized: only allowed files touched; `deploy/docker-compose.fp8.yml`,
  `schemas/openapi.json`, `docker-compose.base.yml`, `webui/**`, `README.md`, `docs/walkthrough.md`,
  `docs/archive/**`, and all `api/**` Python are **byte-unchanged** (`git diff --exit-code` on the frozen
  pair = exit 0).
- **Rendered nvfp4 stack** (grepped the actual `docker compose config` output): a real `vllm-reasoner`
  service (`cosmos3-nano-vllm-reasoner-nvfp4:local`, `--quantization nvfp4_blockwise_w4a16`, no `--omni`),
  **zero** `bf16`/`bfloat`/`layerwise-offload` strings, exactly ONE read-only checkpoint mount for both
  heavy planes — no second/BF16 mount, not an unrendered fragment.
- **INV-4** — no BF16 base/overlay/`WITH_REASONING`; the W4A16 patch drops no stock vLLM method (diffed
  `cosmos3.py`/`quantization__init__.py` vs the frozen FP8 patch — differ only in the sidecar map + the AM
  registration block). Zero-BF16 holds at the same standard the owner-accepted FP8 reasoner meets.
- **INV-5** — `up-nvfp4` = `up --no-start` → `stop vllm-omni vllm-reasoner` → `start api webui`; both heavy
  planes `restart:"no"`; no boot co-load of ~26.9 GiB + ~18 GiB.
- **No hidden BF16 fallback** — the reasoner `RuntimeError`s if the W4A16 method doesn't resolve; it does
  not silently fall back to BF16.
- **Evidence P1/P2** — cover all three modes on NVFP4 off the quantized-only checkpoint; reasoning coherence
  is backed by recorded outputs (not asserted); the shipped patch is byte-identical to the GPU-proven
  prototype AND the reproducible baked image was built+run coherent → the proof transfers.
- **INV-6/INV-7** — no premature default-on; docs uniformly mark NVFP4 reasoning/action quality PENDING.
- **Tests have teeth** — the verifier mutated a sandbox copy: BF16 mount / quant flip / add offload / drop
  reasoner from the stop line each FAIL a specific assertion; it could not construct a green-but-broken state.
- **INV-1** — `test_private_ref_scan` clean; no committed binary.

## Non-blocking observations (already disclosed by the session)
- NVFP4 `assets/` lacks the two action-demo conditioning inputs (WebUI "Run demo" 422s on NVFP4) — recorded
  owner decision, not a repo bug.
- Whole-file vendoring of `quantization/__init__.py` — re-vendor cost on a vLLM bump; pre-existing (FP8
  too), NFR-5 fork-pin follow-up.

## Open item (by design, not a falsification)
The owner's manual per-mode NVFP4 quality gate — the contract's own `done_condition` frames it as the
downstream owner decision; honestly marked PENDING, not over-claimed.
