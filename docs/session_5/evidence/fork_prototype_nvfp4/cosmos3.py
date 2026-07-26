# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

import regex

from vllm.config import VllmConfig
from vllm.model_executor.model_loader.default_loader import DefaultModelLoader
from vllm.model_executor.models.qwen3_vl import Qwen3VLForConditionalGeneration
from vllm.model_executor.models.utils import WeightsMapper


class Cosmos3ForConditionalGeneration(Qwen3VLForConditionalGeneration):
    # Cosmos3 unified checkpoints store a Qwen3-VL understanding tower
    # alongside a generation tower in a flat key layout. This mapper drops
    # the generation tower weights and rewrites the understanding tower keys
    # into the nested form expected by Qwen3VLForConditionalGeneration.
    hf_to_vllm_mapper = WeightsMapper(
        orig_to_new_regex={
            regex.compile(
                r"^(layers\.|embed_tokens\.|norm\.)(.+)$"
            ): r"language_model.model.\1\2",
            regex.compile(
                r"^(blocks\.|merger\.|patch_embed\.|pos_embed\.|deepstack_merger_list\.)"
            ): r"visual.\1",
            regex.compile(r"^audio_modality_embed(?:\..*)?$"): None,
            regex.compile(r"^action_modality_embed(?:\..*)?$"): None,
        },
        orig_to_new_substr={
            "_moe_gen": None,
            ".add_q_proj.": None,
            ".add_k_proj.": None,
            ".add_v_proj.": None,
            ".to_add_out.": None,
            ".norm_added_q.": None,
            ".norm_added_k.": None,
            ".to_q.": ".q_proj.",
            ".to_k.": ".k_proj.",
            ".to_v.": ".v_proj.",
            ".to_out.": ".o_proj.",
            ".norm_q.": ".q_norm.",
            ".norm_k.": ".k_norm.",
            # AM-S5: modelopt NVFP4 blockwise sidecars -> the param names vLLM's
            # ModelOptNvFp4W4A16LinearMethod.create_weights registers. Packed FP4
            # weight (uint8, 2 nibbles/byte) -> `weight`; per-16 FP8 block scale ->
            # `weight_scale`; FP32 per-tensor global scale -> `weight_scale_2`
            # (renamed to weight_global_scale in process_weights_after_loading).
            # Mirrors AM-S2's FP8 `.weight_quantizer._scale`->`.weight_scale` map.
            ".weight_packed": ".weight",
            ".weight_block_scale": ".weight_scale",
            ".weight_global_scale": ".weight_scale_2",
        },
        orig_to_new_prefix={
            "proj_in.": None,
            "proj_out.": None,
            "time_embedder.": None,
            "audio_proj_in.": None,
            "audio_proj_out.": None,
            "action_proj_in.": None,
            "action_proj_out.": None,
            "lm_head.": "language_model.lm_head.",
        },
    )

    allow_patterns_overrides = ["transformer/*.safetensors"]

    """
    Cosmos3 checkpoint separates transformer weights and vision_encoder weights
    into separate directories, as it's in diffusers checkpoint format.
    Using secondary_weights here to load all necessary weights for
    the Reasoner-only part.
    """

    def __init__(self, *, vllm_config: VllmConfig, prefix: str = "") -> None:
        super().__init__(vllm_config=vllm_config, prefix=prefix)
        self.secondary_weights = [
            DefaultModelLoader.Source(
                model_or_path=vllm_config.model_config.model,
                revision=vllm_config.model_config.revision,
                prefix="",
                allow_patterns_overrides=["vision_encoder/*.safetensors"],
            ),
        ]
