"""DiffusersActionAdapter — a typed FD/ID/policy surface over Cosmos3OmniPipeline (Action shell).

``generate_action`` is the only Action. It VALIDATES first (INV-6): an invalid request raises
``ActionValidationFailed`` and never builds ``CosmosActionCondition`` or touches the GPU. It is
deterministic under the request's fixed params (INV-10), reusing the oracle's ``seed_everything`` and
frame normalizer (no new normalizer — the S3 DRY note). Heavy imports are deferred (module imports
torch-free). Refs: session_4/specs/action-engine-adapter.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.base import EngineInfo
from preprocessing.action_schema import ActionMode, ActionSpec, ActionValidationFailed, validate

GUIDANCE_SCALE = 6.0


@dataclass(frozen=True)
class ActionRequest:
    """One deterministic action request (inert Data).

    ``raw_actions`` is the ``[T, raw_action_dim]`` driving tensor (forward dynamics); ``image_path`` /
    ``video_path`` are the trusted-mount conditioning paths (mutually exclusive per mode). ``chunk_size``
    is the action transition count (also the validated 16-400 action-frame window).
    """

    mode: ActionMode
    domain_name: str
    chunk_size: int
    raw_actions: Any | None = None
    image_path: str | None = None
    video_path: str | None = None
    resolution_tier: int = 480
    num_inference_steps: int = 8
    seed: int = 123
    view_point: str = "ego_view"
    prompt: str | None = None
    case_id: str = ""


@dataclass(frozen=True)
class ActionResult:
    """Outputs of one action generation (inert Data the harness compares).

    ``trajectory`` is the predicted ``(T, raw_action_dim)`` actions (``None`` for forward dynamics, which
    predicts video); ``frames`` are decoded H×W×3 float[0,1] arrays (the rollout video, empty for pure
    inverse dynamics); ``info`` records the engine/precision that produced this result.
    """

    case_id: str
    trajectory: Any | None = None
    frames: list[Any] = field(default_factory=list)
    vram_peak_bytes: int = 0
    info: EngineInfo | None = None


def spec_of(request: ActionRequest) -> ActionSpec:
    """Pure Calculation: reduce a request to the validator's ``ActionSpec``.

    ``raw_action_width`` is read from a 2-D non-empty ``raw_actions`` (forward dynamics); ``None`` when
    absent or malformed — a malformed FD tensor then fails validation as a typed error (CONDITION_MISSING),
    never an ``IndexError``. The 16-400 window is applied to ``chunk_size`` by the validator.
    """
    shape = getattr(request.raw_actions, "shape", None) if request.raw_actions is not None else None
    width = int(shape[1]) if shape is not None and len(shape) == 2 and shape[0] >= 1 else None
    return ActionSpec(
        mode=request.mode,
        domain_name=request.domain_name,
        chunk_size=request.chunk_size,
        raw_action_width=width,
        resolution_tier=request.resolution_tier,
        has_image=request.image_path is not None,
        has_video=request.video_path is not None,
    )


def _to_trajectory(action):
    """Calculation over the pipeline output: predicted actions -> (T, raw_dim) float32 numpy (or None)."""
    if action is None:
        return None
    import torch

    tensor = action[0] if isinstance(action, (list, tuple)) else action
    return tensor.detach().to(torch.float32).cpu().numpy()


class DiffusersActionAdapter:
    """FD/ID/policy over a loaded ``Cosmos3OmniPipeline`` with a grafted action head (INV-2).

    Holds one resident pipeline (the runner keeps at most one heavy model resident — 32 GB budget).
    """

    def __init__(self, pipe, info: EngineInfo, device: str = "cuda") -> None:
        self._pipe = pipe
        self._info = info
        self._device = device

    @property
    def info(self) -> EngineInfo:
        return self._info

    def generate_action(self, request: ActionRequest) -> ActionResult:
        """Validate (INV-6) then run one deterministic FD/ID/policy generation (INV-10).

        Raises ``ActionValidationFailed`` (→ 422) BEFORE any pipeline construction when the request is
        invalid. Returns an ``ActionResult`` with the predicted trajectory and/or rollout frames.
        """
        error = validate(spec_of(request))
        if error is not None:
            raise ActionValidationFailed(error)

        # ---- past this point: the request is valid; do GPU work (deferred heavy imports) ----
        import torch
        from diffusers.pipelines.cosmos.pipeline_cosmos3_omni import CosmosActionCondition

        from engines.diffusers_oracle.adapter import _frames_to_float, seed_everything

        image = self._load_image(request.image_path) if request.image_path else None
        video = self._load_video(request.video_path) if request.video_path else None
        cond = CosmosActionCondition(
            mode=request.mode.value,
            chunk_size=request.chunk_size,
            domain_name=request.domain_name,
            resolution_tier=request.resolution_tier,
            raw_actions=request.raw_actions,
            image=image,
            video=video,
            view_point=request.view_point,
        )

        seed_everything(request.seed)
        generator = torch.Generator(device=self._device).manual_seed(request.seed)
        torch.cuda.reset_peak_memory_stats()
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = self._pipe(
                prompt=request.prompt if request.prompt is not None else "",
                action=cond,
                num_inference_steps=request.num_inference_steps,
                guidance_scale=GUIDANCE_SCALE,
                generator=generator,
                output_type="pil",
                return_dict=True,
                enable_safety_check=False,
            )
        torch.cuda.synchronize()
        vram_peak = int(torch.cuda.max_memory_allocated())

        trajectory = _to_trajectory(getattr(out, "action", None))
        frames = _frames_to_float(out.video) if getattr(out, "video", None) is not None else []
        return ActionResult(
            case_id=request.case_id or request.mode.value,
            trajectory=trajectory,
            frames=frames,
            vram_peak_bytes=vram_peak,
            info=self._info,
        )

    @staticmethod
    def _load_image(image_path: str):
        """Action: read a conditioning image from the trusted mount as RGB PIL."""
        from PIL import Image

        return Image.open(image_path).convert("RGB")

    @staticmethod
    def _load_video(video_path: str) -> list:
        """Action: read a conditioning video from the trusted mount as a list of RGB frames."""
        import imageio.v3 as iio

        return list(iio.imiter(video_path))
