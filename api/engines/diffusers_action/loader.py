"""Action enablement by graft (ACD: Actions at the edge + pure merge Calculation; torch-free import).

DORMANT as of AM-S3 (docs/session_3, evidence/P1): action is served by the resident vllm-omni model via
the video-API ``action_mode`` (``engines.vllm_omni.work``), not this in-process graft. The graft is kept
as the pre-authorized ``(c)`` fallback (R-11); it is NOT wired into the default deployment. Its original
premise — that the quantized checkpoint ships **without** action tensors — was **refuted** (E-06): the
``*-Blockwise`` checkpoints now self-contain the bf16 ``action_*`` adapters, so the graft reads them from
the quantized checkpoint itself (no BF16 base; INV-4). The historical sequence it implements:

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

# AM-S3 (INV-4, E-06 refuted): the quantized *-Blockwise checkpoints now SELF-CONTAIN the bf16 action_*
# adapters, and action is served by the resident vllm-omni model (docs/session_3, evidence/P1). This
# in-process graft is DORMANT (kept for the (c) fallback, R-11) and no longer defaults to any BF16 base.
GEN_TOWER_QUANTIZED = 505  # (dormant) weight_quantizer._amax buffers on the GEN tower


@dataclass(frozen=True)
class ActionEngineConfig:
    """Where/how to load the action-enabled engine (inert Data). Precision is detected at load.

    ``quant_dir`` is the quantized checkpoint root (e.g. ``…-NVFP4-Blockwise``). ``base_action_dir`` is an
    OPTIONAL override for where the bf16 ``action_*`` adapters are read from; ``None`` (the default) means
    "read them from ``quant_dir``'s own transformer dir" — the quantized checkpoint self-contains them, so
    **no BF16 base is required** (INV-4).
    """

    quant_dir: str
    base_action_dir: str | None = None
    device: str = "cuda"

    @staticmethod
    def from_env() -> "ActionEngineConfig":
        """Action: read the (operator-controlled, trusted) mounts + device from the environment.

        ``COSMOS3_BASE_ACTION_DIR`` is honored as an explicit override but has **no BF16 default** (INV-4):
        unset → ``None`` → the adapters are read from the quantized checkpoint itself.
        """
        return ActionEngineConfig(
            quant_dir=os.environ.get("COSMOS3_MODEL_DIR", "/data/models/Cosmos3-Nano-FP8-Blockwise"),
            base_action_dir=os.environ.get("COSMOS3_BASE_ACTION_DIR"),
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
    # Dormant graft (R-11): read the bf16 action_* adapters from the explicit override, or — by default —
    # from the quantized transformer dir itself (self-contained; zero-BF16, INV-4). Action is served by
    # the resident omni model (AM-S3), so this path does not run in the default deployment.
    action_dir = config.base_action_dir or transformer_dir
    merged = merge_state_dicts(gen_tensors, read_action_adapter_tensors(action_dir))
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
