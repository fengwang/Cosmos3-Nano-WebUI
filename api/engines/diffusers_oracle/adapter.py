"""DiffusersOracleAdapter — the reference oracle behind EngineAdapter (Action shell).

Heavy imports are deferred into methods (module imports torch-free). ``generate`` is deterministic
under the request's fixed params (INV-10): it seeds everything (incl. ``CUBLAS_WORKSPACE_CONFIG``),
captures the final pre-VAE latents via a step-end callback (M1), decodes frames (``output_type='pil'``
— forcing the VAE decode so the VRAM peak includes it), and records ``max_memory_allocated`` after a
sync. Refs: session_2/specs/diffusers-oracle-adapter.md; quant repo ``src/verify/{loading,generate}``.
"""
from __future__ import annotations

import os
import random

from engines.base import EngineAdapter, EngineInfo, GenerationRequest, GenerationResult


def seed_everything(seed: int) -> None:
    """Action: best-effort global determinism (INV-10).

    Sets ``CUBLAS_WORKSPACE_CONFIG=:4096:8`` (deterministic cuBLAS GEMMs) **before** first cuBLAS use,
    seeds python/numpy/torch RNGs, and enables deterministic algorithms (warn-only — some kernels
    lack deterministic impls). The bands are config-specific, so this must match every comparison.
    """
    import numpy as np
    import torch

    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except Exception:  # noqa: BLE001 — some kernels lack deterministic impls; warn_only handles it
        pass


def _frames_to_float(video) -> list:
    """Normalize the pipeline ``.video`` output to a flat list of HxWx3 float[0,1] arrays.

    Handles a single PIL image, a batched ``[[frame,...]]``, and a flat list of frames.
    """
    import numpy as np
    from PIL import Image

    if isinstance(video, Image.Image):
        seq = [video]
    elif len(video) > 0 and isinstance(video[0], (list, tuple)):
        seq = list(video[0])
    else:
        seq = list(video)

    frames: list = []
    for frame in seq:
        arr = np.asarray(frame)
        arr = arr.astype(np.float32) / 255.0 if arr.dtype == np.uint8 else arr.astype(np.float32)
        frames.append(arr)
    return frames


class DiffusersOracleAdapter(EngineAdapter):
    """Reference oracle wrapping a loaded ``Cosmos3OmniPipeline`` (INV-2).

    ``generate`` is the only Action; ``info`` is the load-time verified metadata. Holds one resident
    pipeline — the runner loads at most one heavy model at a time (32 GB budget).
    """

    def __init__(self, pipe, info: EngineInfo, device: str = "cuda") -> None:
        self._pipe = pipe
        self._info = info
        self._device = device

    @property
    def info(self) -> EngineInfo:
        return self._info

    def warm(self) -> None:
        """Action: a minimal warm pass (single 1-step generation) to warm CUDA kernels + the VAE."""
        self.generate(GenerationRequest(mode="warmup", prompt="a robotic arm", num_inference_steps=1))

    def generate(self, request: GenerationRequest, on_progress=None) -> GenerationResult:
        """Run one deterministic generation; capture latents (CPU f32), frames, audio, VRAM peak."""
        import torch
        from PIL import Image

        seed_everything(request.seed)
        captured: dict = {}

        def _capture(_pipe, step_idx, _t, callback_kwargs):
            if on_progress is not None:
                on_progress(step_idx + 1, request.num_inference_steps)
            latents = callback_kwargs.get("latents")
            if latents is not None:
                captured["latents"] = latents.detach()
            return callback_kwargs

        call_kwargs: dict = dict(
            prompt=request.prompt,
            num_frames=request.num_frames,
            height=request.height,
            width=request.width,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            generator=torch.Generator(device=self._device).manual_seed(request.seed),
            output_type="pil",
            return_dict=True,
            enable_safety_check=False,
            callback_on_step_end=_capture,
            callback_on_step_end_tensor_inputs=["latents"],
        )
        if request.negative_prompt is not None:
            call_kwargs["negative_prompt"] = request.negative_prompt
        if request.image_path:
            call_kwargs["image"] = Image.open(request.image_path).convert("RGB")
        if request.generate_sound:
            import inspect

            # Pass the sound flag only if this pipeline build accepts it (forward-compatible).
            if "enable_sound" in inspect.signature(self._pipe.__call__).parameters:
                call_kwargs["enable_sound"] = True

        torch.cuda.reset_peak_memory_stats()
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = self._pipe(**call_kwargs)
        torch.cuda.synchronize()
        vram_peak = int(torch.cuda.max_memory_allocated())

        latents = captured.get("latents")
        latents = latents.to(torch.float32).cpu() if latents is not None else torch.empty(0)
        return GenerationResult(
            case_id=request.case_id or request.mode,
            latents=latents,
            frames=_frames_to_float(out.video),
            audio=getattr(out, "sound", None),
            vram_peak_bytes=vram_peak,
            info=self._info,
        )
