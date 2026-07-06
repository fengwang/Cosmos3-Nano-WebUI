"""Action enablement by graft (ACD: Actions at the edge + pure merge Calculation; torch-free import).

Enables ``action_gen=True`` on a quantized Cosmos3-Nano checkpoint that ships **without** action tensors,
by grafting the base-model bf16 action adapters. The proven sequence (verified by the S4 smoke probe):

1. build the ``Cosmos3OmniTransformer`` skeleton with ``action_gen=True`` (adds the bf16
   ``action_proj_in/out`` + ``action_modality_embed`` — the 32-domain ``DomainAwareLinear`` heads),
2. ``restore_from_modelopt_state`` (quantizes the GEN tower; the unquantized action modules pass through),
3. ``load_state_dict(strict=True)`` over the **disjoint union** of {quantized GEN weights from the
   ``*-Blockwise`` checkpoint} ∪ {bf16 action adapters from the base model},
4. reuse the oracle's precision verification (GEN-tower count stays 505), then move to the device.

Heavy imports (torch/diffusers/modelopt/safetensors) are deferred into functions, so this module imports
torch-free (the merge Calculation + config are then host-testable).

SECURITY (INV-8): ``modelopt_state.pt`` loads with ``weights_only=False`` (pickle) and the base-model
action shards are read from disk — both load ONLY from the trusted, read-only local model mounts
(``quant_dir`` / ``base_action_dir``), never a request- or network-supplied path.

Refs: session_4/specs/action-enablement.md; reuses ``engines.diffusers_oracle.loader``.
"""
from __future__ import annotations

import glob
import os
from dataclasses import dataclass, replace

from engines.diffusers_oracle.loader import (
    UNIPC_FLOW_SHIFT,
    discover_transformer_dir,
    read_quant_config,
    verify_precision,
)

# The base (unquantized) model that retains the bf16 action adapters stripped from the quantized exports.
DEFAULT_BASE_ACTION_DIR = "/data/models/Cosmos3-Nano/transformer"
GEN_TOWER_QUANTIZED = 505  # weight_quantizer._amax buffers on the GEN tower (action adapters add none)


@dataclass(frozen=True)
class ActionEngineConfig:
    """Where/how to load the action-enabled engine (inert Data). Precision is detected at load.

    ``quant_dir`` is the quantized checkpoint root (e.g. ``…-NVFP4-Blockwise``); ``base_action_dir`` is the
    trusted base-model transformer dir holding the bf16 action adapters.
    """

    quant_dir: str
    base_action_dir: str = DEFAULT_BASE_ACTION_DIR
    device: str = "cuda"

    @staticmethod
    def from_env() -> "ActionEngineConfig":
        """Action: read the (operator-controlled, trusted) mounts + device from the environment."""
        return ActionEngineConfig(
            quant_dir=os.environ.get("COSMOS3_MODEL_DIR", "/data/models/Cosmos3-Nano-FP8-Blockwise"),
            base_action_dir=os.environ.get("COSMOS3_BASE_ACTION_DIR", DEFAULT_BASE_ACTION_DIR),
            device=os.environ.get("COSMOS3_DEVICE", "cuda"),
        )


def merge_state_dicts(gen: dict, adapters: dict) -> dict:
    """Pure Calculation: disjoint union of the GEN weights and the action adapters.

    Raises ``ValueError`` on any key collision (the graft must be additive — the GEN tower and the action
    adapters occupy disjoint key spaces). Inputs are not mutated; a new dict is returned.
    """
    overlap = gen.keys() & adapters.keys()
    if overlap:
        raise ValueError(f"action graft key collision (GEN ∩ adapters): {sorted(overlap)}")
    return {**gen, **adapters}


def read_action_adapter_tensors(base_action_dir: str) -> dict:
    """Action: load the ``action_*`` bf16 tensors from the trusted base-model transformer shards.

    Returns only the action-adapter keys (``action_modality_embed``, ``action_proj_in.*``,
    ``action_proj_out.*``); never the large GEN tower. Uses ``safe_open`` + selective ``get_tensor`` so
    only the action tensors' byte ranges are read (not the full multi-GB shards). Raises
    ``FileNotFoundError`` if none are found (a base model without action adapters cannot enable action).
    """
    from safetensors import safe_open

    tensors: dict = {}
    for shard in sorted(glob.glob(f"{base_action_dir}/*.safetensors")):
        with safe_open(shard, framework="pt", device="cpu") as handle:
            for key in handle.keys():
                if key.startswith("action_"):
                    tensors[key] = handle.get_tensor(key)
    if not tensors:
        raise FileNotFoundError(f"no action_* adapter tensors under {base_action_dir!r}")
    return tensors


def load_action_transformer(config: ActionEngineConfig):
    """Action: materialize the action-enabled quantized transformer on CPU (grafted, precision-verified).

    Returns ``(transformer, EngineInfo)``. The caller moves the assembled pipeline to the device after
    (NVFP4 restore is device-order sensitive). Verification runs on the CPU transformer so a precision
    mismatch fails fast. The returned ``EngineInfo.engine == "diffusers_action"``.
    """
    import modelopt.torch.opt as mto
    import torch
    from diffusers import Cosmos3OmniTransformer
    from safetensors.torch import load_file

    transformer_dir = discover_transformer_dir(config.quant_dir)
    cfg = {**Cosmos3OmniTransformer.load_config(f"{transformer_dir}/config.json"), "action_gen": True}
    transformer = Cosmos3OmniTransformer.from_config(cfg).to(torch.bfloat16)
    # INV-8: pickle sidecar — trusted local mount only.
    state = torch.load(f"{transformer_dir}/modelopt_state.pt", weights_only=False)
    restored = mto.restore_from_modelopt_state(transformer, state)
    if restored is not None:
        transformer = restored

    gen_tensors: dict = {}
    for shard in sorted(glob.glob(f"{transformer_dir}/*.safetensors")):
        gen_tensors.update(load_file(shard))
    merged = merge_state_dicts(gen_tensors, read_action_adapter_tensors(config.base_action_dir))
    transformer.load_state_dict(merged, strict=True)

    info = verify_precision(
        transformer, read_quant_config(config.quant_dir), config.quant_dir, expected_quantized=GEN_TOWER_QUANTIZED
    )
    return transformer, replace(info, engine="diffusers_action")


def build_action_pipeline(config: ActionEngineConfig, transformer):
    """Action: assemble the GPU-resident diffusers pipeline around the grafted transformer.

    Mirrors the oracle's pipeline assembly (UniPC ``flow_shift``, safety off). The pipeline stays
    resident on the target device; VAE tiling is enabled to fit high-resolution decode within VRAM.
    """
    import torch
    from diffusers import Cosmos3OmniPipeline, UniPCMultistepScheduler

    pipe = Cosmos3OmniPipeline.from_pretrained(
        config.quant_dir, transformer=transformer, torch_dtype=torch.bfloat16, enable_safety_checker=False
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=UNIPC_FLOW_SHIFT)
    pipe = pipe.to(config.device)
    pipe.enable_vae_tiling()
    return pipe


def build_action_engine(config: ActionEngineConfig):
    """Action facade: load (CPU) -> verify -> assemble pipeline (device) -> ``DiffusersActionAdapter``."""
    from engines.diffusers_action.adapter import DiffusersActionAdapter

    transformer, info = load_action_transformer(config)
    pipe = build_action_pipeline(config, transformer)
    return DiffusersActionAdapter(pipe, info, device=config.device)
