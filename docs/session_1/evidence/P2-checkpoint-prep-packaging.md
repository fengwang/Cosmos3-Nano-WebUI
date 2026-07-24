# P2 Evidence — `tools/checkpoint_prep` zero-BF16 action packaging (result: **GO — already applied**)

Date: 2026-07-24. Read-only evaluation (the toolkit is forbidden to modify this
session). Spec referenced by the code: `docs/session_5/specs/fp8-checkpoint-mutation.md`
(a **prior P6-era** effort, tags P6-S5/P6-S6 — predates this AM blueprint).

## The toolkit (CLI `python -m checkpoint_prep …`)
- **`mutate`** — help: *"append action tensors + restore BF16 lm_head"*. The
  zero-BF16 action packaging operation.
- `self-contained` / `copy_shared` — copy shared serve-time files + a **BF16
  reasoner bundle** into a `-dist` dir (this built `…-FP8-Blockwise-dist`, P6-S6).
- `probe` — integrity probe; `snapshot` — pre-mutation facts + per-tensor sha256;
  `restore` — roll back from `*.s5-orig.bak`; `verify-self-contained`.

## The mutation recipe (`mutation.py`, pure Calculation core)
- `ACTION_TENSORS` = the exact 5 keys found on-disk (comment: *"dropped from FP8
  during quantization, present in the BF16 source + NVFP4"*).
- `DROPPED_LMHEAD` = 3 FP8 lm_head tensors replaced by 1 BF16 `lm_head.weight`.
- `plan_mutation`: validates each added tensor is **BF16** with **config-derived
  shape** (R-11), and **refuses to double-apply** if already mutated (fail-closed).
- `build_layout`: recomputes a contiguous data block + 8-byte-aligned header
  (kept tensors keep byte length; offsets recomputed).
- `updated_sidecars`: updates `quantization_config.json` + `quantizer_map_diff.json`
  — **`n_quantized 217 → 216`** (lm_head un-quantized). This is exactly the 216 my
  P1 scan measured, and explains why the in-process loader's `GEN_TOWER_QUANTIZED=505`
  is stale (D1).

## Proof it was already applied to the deployed + public checkpoints
- Deployed `…-FP8-Blockwise/quantizer_map_diff.json`:
  `note: "P6-S5: appended 5 BF16 action tensors + restored BF16 lm_head …"`,
  `n_weight_quantized: 216`, `appended_action_keys` = the 5, `lm_head_restored_bf16:
  true`. HEAD commit `4e181f9 "lm_head back to bf16"` touched exactly
  `quantization_config.json`, `quantizer_map_diff.json`, `transformer/config.json`,
  `transformer/diffusion_pytorch_model.safetensors`. `.s5-orig.bak` files = the
  `mutate --backup` snapshots.
- Pinned **public** rev `9bf5d6ae` also carries the 5 action tensors (P1, HF
  range-read) → a fresh `hf download` is already action-ready.

## Verdict (rubric)
- **Zero-BF16 action packaging = `bundle-via-checkpoint_prep` GO — and ALREADY
  DONE.** E-06's gap was real *at raw-quantization time* and was **closed by the
  P6-S5 `mutate` tool**; the current pinned + deployed checkpoints ship the BF16
  action adapters. The tool is documented, unit-tested (`tests/checkpoint_prep/**`),
  integrity-probed, and backup/restore-safe — it satisfies R-10 (no in-place
  corruption) and supports NFR-5 (pin a new revision).
- **Caveat for AM-S3:** the *serving code* was **not** reconciled to the mutated
  checkpoint — `diffusers_action/loader.py` still grafts `action_*` from the BF16
  base and collides (P5), and `GEN_TOWER_QUANTIZED=505` ≠ 216. AM-S3's action work
  is code-side (use the checkpoint's own tensors), not packaging.
