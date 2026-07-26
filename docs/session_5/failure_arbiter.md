# AM-S5 Failure Arbiter Log

Failures classified before any fix, per `docs/agent_workflow/prompts/failure_arbiter.md`.

## F1 — NVFP4 reasoner patch: circular import at registration (probe)
- **Symptom:** `AM-S5: failed to register nvfp4_blockwise_w4a16: cannot import name 'ParallelConfig'
  from partially initialized module 'vllm.config' (circular import)` → serving aborted with
  `Unknown quantization method: nvfp4_blockwise_w4a16`.
- **Classification: BUG** (my patch violated the AM-S2 import discipline). The first prototype imported
  `vllm...modelopt` at module top; registering it in `quantization/__init__` ran that import before
  `vllm.config` was initialized.
- **Fix:** import only `base_config` at module top; defer `modelopt`/`linear` into `_base_config()` /
  `get_quant_method()` (exactly the AM-S2 FP8 pattern). Re-probed → registered + coherent (evidence/P2).
- **Regression guard / eval seed:** `EV-AM-QUANT-PLUGIN-IMPORT-TIMING`.

## F2 — Private path committed in the staged reproduction script (CPU suite)
- **Symptom:** `tests/test_private_ref_scan.py` failed with a `home_path` finding at
  `docs/session_5/evidence/fork_prototype_nvfp4/probe_action_nvfp4.py:14` — a private home-cache absolute
  path (a `/home/<user-cache>/…/scratchpad` constant) baked into the staged probe script.
- **Classification: BUG** (INV-1 violation in a staged artifact — a private home path baked into the
  probe script's scratch-dir constant). The scanner correctly caught it.
- **Fix:** replace the hardcoded scratch path with `os.environ.get("AMS5_SCRATCH", os.path.join(
  os.getcwd(), "scratch", "ams5"))`. Scanner re-run clean; full CPU suite green.

## Non-failures (checked, correctly NOT product-code fixes)
- Sharded-review Low/Nit findings (VRAM comment drift, R-05 bookkeeping) — TEST/DOC accuracy, not BUGs;
  the two cheap ones applied, the rest dispositioned in `sharded_review.md`.
- The `/data/models/...` absolute path in evidence — NOT an INV-1 violation (established public
  container-mount convention; the scanner flags only `/data/home*`), so no fix.
