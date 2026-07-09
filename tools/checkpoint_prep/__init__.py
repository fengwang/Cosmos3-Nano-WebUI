"""checkpoint_prep — in-repo tool to prepare Cosmos3-Nano `-dist` checkpoints.

Session 5 (`P6-S5`): append the BF16 action tensors and restore the BF16 `lm_head` into the FP8-dist
transformer, preserving every other pre-existing tensor byte-identical (INV-11, scoped `lm_head`
exception), then verify with an integrity probe. Designed for S6 reuse (shared-file copy).

ACD split:
- `safetensors_io` + `mutation`  : pure Calculations (parse/build headers, plan the mutation, lay out
                                    offsets, recompute sidecars) — torch-free, unit-tested on fixtures.
- `rewrite`                       : Actions (chunked raw-byte copy, hashing, atomic replace + backup).
- `integrity_probe`               : the deterministic verification (predicates + CLI).
"""
