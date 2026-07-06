"""Pure mutation core — decide/lay-out the FP8 checkpoint mutation and recompute sidecars.

All functions here are pure Calculations over header dicts (name -> {dtype, shape, data_offsets}); no
file I/O, no torch. The effectful rewrite lives in `rewrite.py`. Spec:
docs/session_5/specs/fp8-checkpoint-mutation.md.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

from checkpoint_prep.safetensors_io import build_header_bytes

# The 5 BF16 action tensors dropped from FP8 during quantization (present in the BF16 source + NVFP4).
ACTION_TENSORS: tuple[str, ...] = (
    "action_modality_embed",
    "action_proj_in.bias.weight",
    "action_proj_in.fc.weight",
    "action_proj_out.bias.weight",
    "action_proj_out.fc.weight",
)
# The 3 FP8 lm_head tensors removed and replaced by a single BF16 lm_head.weight (INV-7 restore).
DROPPED_LMHEAD: tuple[str, ...] = (
    "lm_head.weight",
    "lm_head.weight_quantizer._amax",
    "lm_head.weight_quantizer._scale",
)
# Tensors added from the BF16 source (all BF16).
ADDED_TENSORS: tuple[str, ...] = (*ACTION_TENSORS, "lm_head.weight")


class MutationError(RuntimeError):
    """Raised when the planned mutation is unsafe (bad source dtype/shape, missing tensor, already
    mutated). Fail-closed: no rewrite is attempted."""


@dataclass(frozen=True)
class MutationPlan:
    keep: tuple  # names copied verbatim from the FP8 source file (all pre-existing minus `drop`)
    drop: tuple  # names removed (the FP8 lm_head + its 2 quantizer sidecars)
    add: tuple   # names sourced BF16 from the source model (5 action + lm_head.weight)


@dataclass(frozen=True)
class Layout:
    order: tuple            # emission order (kept by ascending original offset, then added)
    entries: dict           # name -> {dtype, shape, data_offsets:[s,e]} at the new contiguous offsets
    header_len: int         # N (bytes of JSON header, 8-byte aligned)
    data_len: int           # total data-block length


def expected_shapes(cfg: dict) -> dict:
    """Config-derived expected shapes for the added tensors (R-11 defense)."""
    h, d = cfg["hidden_size"], cfg["action_dim"]
    n, v = cfg["num_embodiment_domains"], cfg["vocab_size"]
    return {
        "action_modality_embed": [h],
        "action_proj_in.bias.weight": [n, h],
        "action_proj_in.fc.weight": [n, d * h],
        "action_proj_out.bias.weight": [n, d],
        "action_proj_out.fc.weight": [n, d * h],
        "lm_head.weight": [v, h],
    }


def _names(header: dict) -> set:
    return {k for k in header if k != "__metadata__"}


def plan_mutation(fp8_header: dict, bf16_src: dict, cfg: dict) -> MutationPlan:
    """Pure Calculation: decide keep/drop/add, validating each added tensor's dtype+shape.

    Refuses (MutationError) on a wrong/missing source tensor or when the checkpoint is already mutated.
    """
    names = _names(fp8_header)

    already = set(ACTION_TENSORS).issubset(names) and (
        fp8_header.get("lm_head.weight", {}).get("dtype") == "BF16"
    )
    if already:
        raise MutationError(
            "checkpoint already mutated: action tensors present and lm_head is BF16 (refusing to "
            "double-apply)"
        )

    exp = expected_shapes(cfg)
    for name in ADDED_TENSORS:
        ref = bf16_src.get(name)
        if ref is None:
            raise MutationError(f"missing BF16 source tensor: {name}")
        dtype = str(ref.get("dtype", ""))
        if dtype != "BF16":
            raise MutationError(f"source tensor {name} dtype {dtype!r} != BF16 (R-11)")
        shape = list(ref.get("shape", []))
        if name in exp and shape != exp[name]:
            raise MutationError(
                f"source tensor {name} shape {shape} != config-expected {exp[name]} (R-11)"
            )

    drop = tuple(n for n in DROPPED_LMHEAD if n in names)
    keep = tuple(n for n in names if n not in DROPPED_LMHEAD)
    return MutationPlan(keep=keep, drop=drop, add=ADDED_TENSORS)


def _size(entry: dict) -> int:
    s, e = entry["data_offsets"]
    return e - s


def build_layout(plan: MutationPlan, fp8_header: dict, bf16_src: dict) -> Layout:
    """Pure Calculation: recompute a contiguous data block (kept-by-original-offset, then added) and the
    8-byte-aligned header. Kept tensors preserve their byte length; only offsets are recomputed."""
    kept_ordered = sorted(plan.keep, key=lambda n: fp8_header[n]["data_offsets"][0])
    order = (*kept_ordered, *plan.add)

    entries: dict = {}
    cursor = 0
    for name in order:
        src = fp8_header[name] if name in fp8_header and name in plan.keep else bf16_src[name]
        size = _size(src)
        entries[name] = {
            "dtype": src["dtype"],
            "shape": list(src["shape"]),
            "data_offsets": [cursor, cursor + size],
        }
        cursor += size

    header_bytes = build_header_bytes(entries)
    header_len = len(header_bytes) - 8
    return Layout(order=order, entries=entries, header_len=header_len, data_len=cursor)


def updated_sidecars(
    quantization_config: dict, quantizer_map_diff: dict, dropped_scale_elements: int = 0
) -> tuple[dict, dict]:
    """Pure Calculation: return updated (quantization_config, quantizer_map_diff) reflecting the mutation.

    lm_head is no longer quantized (INV-7 restored) → n_quantized 217->216, quant_lmhead false, lm_head
    dropped from the quantized set, scale counts decremented; the action keys are marked resolved. The
    `recipe` is preserved (load-bearing: `fp8_w8a16_selected` keys on it). Inputs are not mutated.
    """
    qc = copy.deepcopy(quantization_config)
    qmd = copy.deepcopy(quantizer_map_diff)

    qc["quant_lmhead"] = False
    mp = qc.get("mixed_precision", {})
    mp["quantized"] = [p for p in mp.get("quantized", []) if p != "lm_head"]
    if "n_quantized" in mp:
        mp["n_quantized"] = mp["n_quantized"] - 1
    qc["mixed_precision"] = mp

    sl = qc.get("scale_layout")
    if sl is not None:
        if "n_quantized_weight" in sl:
            sl["n_quantized_weight"] = sl["n_quantized_weight"] - 1
            sl["n_scale"] = 2 * sl["n_quantized_weight"]
        if "total_scale_elements" in sl:
            sl["total_scale_elements"] = sl["total_scale_elements"] - dropped_scale_elements
        ex = sl.get("example_shapes")
        if isinstance(ex, dict):
            sl["example_shapes"] = {
                k: v for k, v in ex.items()
                if not (isinstance(v, dict) and v.get("module_example") == "lm_head")
            }
        qc["scale_layout"] = sl

    if "n_weight_quantized" in qmd:
        qmd["n_weight_quantized"] = qmd["n_weight_quantized"] - 1
    if "expected_quantized_count" in qmd:
        qmd["expected_quantized_count"] = qmd["expected_quantized_count"] - 1
    qmd["dropped_action_keys"] = []
    qmd["appended_action_keys"] = list(ACTION_TENSORS)
    qmd["lm_head_restored_bf16"] = True
    qmd["note"] = (
        "P6-S5: appended 5 BF16 action tensors + restored BF16 lm_head from the BF16 source; "
        "quantized set is now mlp.*/mlp_moe_gen.* only (INV-7 restored)."
    )
    return qc, qmd
