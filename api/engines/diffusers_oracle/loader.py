"""Oracle loading (ACD: Actions at the edge + pure path/verify Calculations).

Proven **Path-B** safetensors load (never the large `.pt`): ``from_config(action_gen=False)`` ->
``restore_from_modelopt_state`` (tiny structural sidecar) -> ``load_state_dict(strict=True)``,
restored on **CPU** then the whole pipeline moved to the device together (NVFP4 is device-order
sensitive). Heavy imports (torch/diffusers/modelopt/safetensors) are **deferred into functions**, so
this module imports torch-free (discovery/verify path logic is then host-testable).

SECURITY (INV-8): ``modelopt_state.pt`` is loaded with ``weights_only=False`` (pickle). Load it ONLY
from the trusted, read-only ``COSMOS3_MODEL_DIR`` mount — never a request- or network-supplied path.

Refs: session_2/specs/diffusers-oracle-adapter.md; model-dir ``load_quantized.py``.
"""
from __future__ import annotations

import glob
import json
import os

from engines.base import EngineInfo, Precision
from engines.diffusers_oracle.config import OracleConfig, precision_from_quant_config

UNIPC_FLOW_SHIFT = 10.0


class OraclePrecisionError(RuntimeError):
    """Raised when the loaded transformer's precision does not match the checkpoint's declaration.

    Propagated (never masked): we refuse to serve an engine whose actual precision we cannot confirm.
    """


def discover_transformer_dir(root: str) -> str:
    """Find the dir holding the transformer ``*.safetensors`` + ``modelopt_state.pt`` + ``config.json``.

    Action (filesystem). Tolerates the nested NVFP4-Blockwise layout (``transformer/transformer/``) and the
    flat FP8-Blockwise one (``transformer/``), checking most-nested first. Raises ``FileNotFoundError``
    naming the directories tried.
    """
    tried: list[str] = []
    for cand in (f"{root}/transformer/transformer", f"{root}/transformer", root):
        tried.append(cand)
        if (
            glob.glob(f"{cand}/*.safetensors")
            and os.path.exists(f"{cand}/modelopt_state.pt")
            and os.path.exists(f"{cand}/config.json")
        ):
            return cand
    raise FileNotFoundError(f"no transformer safetensors+sidecar+config under any of: {tried}")


def read_quant_config(root: str) -> dict:
    """Action: read ``{root}/quantization_config.json`` (the precision declaration). ``{}`` if absent."""
    path = f"{root}/quantization_config.json"
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return json.load(fh)


def load_transformer(transformer_dir: str):
    """Action: materialize the quantized ``Cosmos3OmniTransformer`` from safetensors + sidecar, on CPU.

    The caller moves the assembled pipeline to the GPU afterward — restoring NVFP4 directly onto CUDA
    splits the packed-data/block-scale/global-scale across devices. Never opens the large ``.pt``.
    """
    import modelopt.torch.opt as mto
    import torch
    from diffusers import Cosmos3OmniTransformer
    from safetensors.torch import load_file

    cfg = {**Cosmos3OmniTransformer.load_config(f"{transformer_dir}/config.json"), "action_gen": False}
    transformer = Cosmos3OmniTransformer.from_config(cfg).to(torch.bfloat16)
    # INV-8: pickle sidecar — trusted local mount only.
    state = torch.load(f"{transformer_dir}/modelopt_state.pt", weights_only=False)
    restored = mto.restore_from_modelopt_state(transformer, state)
    if restored is not None:
        transformer = restored
    tensors: dict = {}
    for shard in sorted(glob.glob(f"{transformer_dir}/*.safetensors")):
        tensors.update(load_file(shard))
    transformer.load_state_dict(tensors, strict=True)
    return transformer


def load_pipeline(config: OracleConfig, transformer):
    """Action: inject ``transformer`` into the diffusers pipeline (UniPC ``flow_shift``, safety off).

    The pipeline's other modules (VAE, vision encoder, tokenizers) load from ``config.model_dir``'s
    subdirs; the whole assembled pipeline is moved to ``config.device`` together.
    """
    import torch
    from diffusers import Cosmos3OmniPipeline, UniPCMultistepScheduler

    pipe = Cosmos3OmniPipeline.from_pretrained(
        config.model_dir, transformer=transformer, torch_dtype=torch.bfloat16, enable_safety_checker=False
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=UNIPC_FLOW_SHIFT)
    return pipe.to(config.device)


def observe_precision(transformer) -> tuple[Precision, int]:
    """Calculation over the loaded module: ``(precision-from-weights, n_quantized)``.

    Discriminator (validated on the real checkpoints): NVFP4-AWQ uses **two-level** scaling — a
    per-block-16 E4M3 ``weight_quantizer._scale`` **plus** a per-tensor FP32
    ``weight_quantizer._double_scale`` global scale — so the presence of ``_double_scale`` marks
    NVFP4; per-tensor FP8 has only a single ``_scale`` and no ``_double_scale``. ``n_quantized`` =
    number of ``weight_quantizer._amax`` buffers (one per quantized weight; 505 on this model).
    Pure: reads the module's ``state_dict`` (no I/O, no mutation).
    """
    sd = transformer.state_dict()
    n_quantized = sum(1 for k in sd if k.endswith("weight_quantizer._amax"))
    has_double_scale = any(k.endswith("weight_quantizer._double_scale") for k in sd)
    return (Precision.NVFP4 if has_double_scale else Precision.FP8), n_quantized


def verify_precision(
    transformer, quant_cfg: dict, checkpoint_dir: str, expected_quantized: int = 505
) -> EngineInfo:
    """Verify the loaded precision matches the checkpoint's declaration; raise on mismatch.

    Two integrity gates (both SHALL raise — never serve an engine we can't confirm):
    1. the dir's ``quantization_config.json`` (``declared``) must agree with the precision inferred
       from the loaded weights' scale layout (``observed``) — defeats a silent FP8-as-NVFP4 mislabel;
    2. the count of quantized modules must equal ``expected_quantized`` (505 on this model) — catches
       a partial/corrupt restore that still trips the precision discriminator.
    Returns the verified ``EngineInfo``.
    """
    declared, granularity = precision_from_quant_config(quant_cfg)
    observed, n_quantized = observe_precision(transformer)
    if observed is not declared:
        raise OraclePrecisionError(
            f"{checkpoint_dir}: declared {declared.value} but the loaded weights are {observed.value} "
            f"(n_quantized={n_quantized})"
        )
    if n_quantized != expected_quantized:
        raise OraclePrecisionError(
            f"{checkpoint_dir}: expected {expected_quantized} quantized modules but loaded {n_quantized} "
            f"(partial/corrupt restore?)"
        )
    return EngineInfo(
        engine="diffusers_oracle",
        precision=declared,
        checkpoint_dir=checkpoint_dir,
        n_quantized=n_quantized,
        granularity=granularity,
        recipe=str(quant_cfg.get("recipe", "")),
    )


def build_oracle(config: OracleConfig):
    """Action facade: discover -> load (CPU) -> verify precision -> assemble pipeline -> adapter.

    Verification runs on the CPU-loaded transformer before it is moved to the GPU, so a precision
    mismatch fails fast (before paying the pipeline-assembly + device-transfer cost).
    """
    from engines.diffusers_oracle.adapter import DiffusersOracleAdapter

    transformer_dir = discover_transformer_dir(config.model_dir)
    transformer = load_transformer(transformer_dir)
    info = verify_precision(transformer, read_quant_config(config.model_dir), config.model_dir)
    pipe = load_pipeline(config, transformer)
    return DiffusersOracleAdapter(pipe, info, device=config.device)
