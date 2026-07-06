"""Fail-closed reasoner-source guard (ACD: Data + a pure Calculation + a thin header-reading Action).

The reasoner loads the *understanding tower* from ``<dir>/transformer/*.safetensors``
(``Cosmos3ForConditionalGeneration.allow_patterns_overrides`` in
the vLLM Cosmos3 model definition): it keeps the ``WeightsMapper``-kept keys (``layers.*``,
``embed_tokens``, ``norm``, ``lm_head``, and the visual ``blocks.*``/``merger``/``patch_embed``/
``pos_embed``/``deepstack_merger_list``) and drops the generation tower (``*_moe_gen``, ``proj_in/out``,
``time_embedder``, ``audio_*``, ``action_*``, diffusion-attn adds). In the blockwise-quantized checkpoints those
reasoner-kept FFNs (``layers.*.mlp.*``) are blockwise-quantized (FP8 ``F8_E4M3`` / NVFP4 ``weight_packed``),
which the plain-vLLM reasoner cannot dequant — and the existing bf16 identity gate only fires *after* a
wasted load, on the *config* dtype, never the *weight* dtype.

This module decides, from the safetensors header alone (torch-free, no GPU) and BEFORE any load, whether a
candidate reasoner source is a servable BF16 understanding tower. It is the S6 pre-``vllm serve`` preflight
(``python -m engines.vllm.reasoner_preflight <dir>``) and the ``build_reasoner`` fail-fast. Refs:
docs/session_4/specs/reasoner-source-guard.md; design.md D-4.
"""
from __future__ import annotations

import json
import re
import struct
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Keep/drop pinned to the reasoner WeightsMapper (the vLLM Cosmos3 model definition).
_KEEP = re.compile(
    r"^(layers\.|embed_tokens\.|norm\.|lm_head\.|blocks\.|merger\.|patch_embed\.|pos_embed\.|deepstack_merger_list\.)"
)
_DROP_SUBSTR = (
    "_moe_gen", ".add_q_proj.", ".add_k_proj.", ".add_v_proj.", ".to_add_out.",
    ".norm_added_q.", ".norm_added_k.",
)
_DROP_PREFIX = (
    "proj_in.", "proj_out.", "time_embedder.", "audio_proj_in.", "audio_proj_out.",
    "action_proj_in.", "action_proj_out.", "audio_modality_embed", "action_modality_embed",
)
# Known quantized *weight* dtypes (denylist, not a bf16 allowlist — so legitimate int/bool buffers among
# kept tensors are not mistaken for quantized weights). FP8 (modelopt) + int8; NVFP4 packing is caught by
# the sidecar suffix below (its packed tensor is ``U8`` but named ``*.weight_packed``).
_QUANT_WEIGHT_DTYPES = frozenset({"F8_E4M3", "F8_E4M3FN", "F8_E5M2", "I8", "INT8"})
# Blockwise-quant sidecar name suffixes (FP8 modelopt ``_quantizer.*`` + NVFP4 ``weight_*_scale``/packed).
_QUANT_SIDECAR_SUFFIX = (
    "weight_packed", "weight_block_scale", "weight_global_scale",
    "weight_quantizer._amax", "weight_quantizer._scale",
)
# A real safetensors header is ~KB–MB. An implausibly large declared length means a corrupt or hostile
# file; cap it and fail closed rather than attempt a multi-GiB allocation (defense-in-depth, sharded review).
_MAX_HEADER_BYTES = 128 * 1024 * 1024


class ReasonerSourceErrorCode(Enum):
    """Why a candidate reasoner source is not a servable BF16 understanding tower (no string blindness)."""

    QUANTIZED_WEIGHT = "quantized_reasoner_weight"
    QUANT_SIDECAR = "quant_sidecar_present"
    EMPTY_UNDERSTANDING_TOWER = "empty_understanding_tower"
    NO_TRANSFORMER_WEIGHTS = "no_transformer_weights"
    MALFORMED_HEADER = "malformed_safetensors_header"


@dataclass(frozen=True)
class ReasonerSourceRejection:
    """A structured, typed rejection (inert Data — no bool/null blindness)."""

    code: ReasonerSourceErrorCode
    message: str
    tensor: str | None = None
    dtype: str | None = None


class ReasonerSourceError(RuntimeError):
    """Raised to refuse serving BEFORE any model load; carries the typed rejection."""

    def __init__(self, rejection: ReasonerSourceRejection) -> None:
        self.rejection = rejection
        super().__init__(f"{rejection.code.value}: {rejection.message}")


def _is_dropped(name: str) -> bool:
    """Calculation: does the reasoner WeightsMapper drop this key (generation tower)?"""
    return any(s in name for s in _DROP_SUBSTR) or any(name.startswith(p) for p in _DROP_PREFIX)


def _is_kept(name: str) -> bool:
    """Calculation: does the reasoner keep this key (understanding tower)?"""
    return bool(_KEEP.match(name)) and not _is_dropped(name)


def reasoner_source_verdict(headers: dict) -> ReasonerSourceRejection | None:
    """Pure Calculation over safetensors header metadata: ``None`` == servable BF16 reasoner source.

    ``headers`` maps tensor name -> a dict carrying at least ``"dtype"`` (the safetensors header with
    ``__metadata__`` removed). Rejects when any reasoner-**kept** tensor carries a blockwise-quant sidecar
    or is a quantized ``.weight`` dtype, or when the kept understanding tower has no weight tensors.
    Reasoner-**dropped** generation-tower quantization is ignored (the reasoner never loads it).
    """
    kept_weight_seen = False
    for name, meta in headers.items():
        if not _is_kept(name):
            continue
        if any(name.endswith(suffix) for suffix in _QUANT_SIDECAR_SUFFIX):
            return ReasonerSourceRejection(
                ReasonerSourceErrorCode.QUANT_SIDECAR,
                f"reasoner-kept blockwise-quant sidecar present: {name}",
                tensor=name,
            )
        if name.endswith(".weight"):
            dtype = str(meta.get("dtype", "")).upper()
            if dtype in _QUANT_WEIGHT_DTYPES:
                return ReasonerSourceRejection(
                    ReasonerSourceErrorCode.QUANTIZED_WEIGHT,
                    f"reasoner-kept weight {name} has quantized dtype {dtype}",
                    tensor=name,
                    dtype=dtype,
                )
            kept_weight_seen = True
    if not kept_weight_seen:
        return ReasonerSourceRejection(
            ReasonerSourceErrorCode.EMPTY_UNDERSTANDING_TOWER,
            "no reasoner-kept understanding-tower weight tensors found in transformer headers",
        )
    return None


def _read_safetensors_header(path: Path) -> dict:
    """Action: read one safetensors file's header JSON (the leading u64-length-prefixed metadata block)."""
    with open(path, "rb") as handle:
        length = struct.unpack("<Q", handle.read(8))[0]
        if not 0 < length <= _MAX_HEADER_BYTES:
            raise ReasonerSourceError(
                ReasonerSourceRejection(
                    ReasonerSourceErrorCode.MALFORMED_HEADER,
                    f"{path.name}: safetensors header length {length} is implausible "
                    f"(expected 1..{_MAX_HEADER_BYTES}) — corrupt or hostile file",
                )
            )
        header = json.loads(handle.read(length))
    header.pop("__metadata__", None)
    return header


def read_transformer_headers(model_dir: str) -> dict:
    """Action: merge the headers of all ``<model_dir>/transformer/*.safetensors`` (the reasoner primary source).

    Raises ``ReasonerSourceError`` (``NO_TRANSFORMER_WEIGHTS``) if the directory has no such files — the
    reasoner's ``allow_patterns_overrides`` targets exactly this glob, so an empty match is unservable.
    """
    files = sorted((Path(model_dir) / "transformer").glob("*.safetensors"))
    if not files:
        raise ReasonerSourceError(
            ReasonerSourceRejection(
                ReasonerSourceErrorCode.NO_TRANSFORMER_WEIGHTS,
                f"no transformer/*.safetensors under {model_dir}",
            )
        )
    merged: dict = {}
    for path in files:
        merged.update(_read_safetensors_header(path))
    return merged


def assert_reasoner_source(model_dir: str) -> None:
    """Action: raise ``ReasonerSourceError`` unless ``model_dir`` is a servable BF16 reasoner source."""
    rejection = reasoner_source_verdict(read_transformer_headers(model_dir))
    if rejection is not None:
        raise ReasonerSourceError(rejection)


def _main(argv: list[str]) -> int:
    """CLI: exit 0 if servable, 1 with the typed reason if not, 2 on usage error. No GPU, no torch."""
    import sys

    if len(argv) != 1:
        print("usage: python -m engines.vllm.reasoner_preflight <model_dir>", file=sys.stderr)
        return 2
    try:
        assert_reasoner_source(argv[0])
    except ReasonerSourceError as exc:
        print(f"REJECT {exc.rejection.code.value}: {exc.rejection.message}", file=sys.stderr)
        return 1
    print(f"OK servable bf16 reasoner source: {argv[0]}")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(_main(sys.argv[1:]))
