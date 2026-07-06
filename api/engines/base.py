"""The EngineAdapter contract + its immutable Data (ACD: Data + one Action method).

The equivalence harness drives two `EngineAdapter`s and compares their `GenerationResult`s
to a band verdict — the INV-3 mechanism S3's TRT-LLM adapter reuses unchanged. This module is
deliberately **torch-free at import**: tensors/frames are typed `Any` and no heavy ML library is
imported at module scope, so the torch-free server and host-test loop can import the interface.
Concrete adapters (e.g. `diffusers_oracle`) own all GPU I/O and defer their heavy imports.

Refs: session_2/specs/engine-adapter-interface.md; evidence_map INV-2/INV-3.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Precision(Enum):
    """The numeric precision an engine actually ran (not a bare bool/string — no precision blindness)."""

    NVFP4 = "nvfp4"
    FP8 = "fp8"
    BF16 = "bf16"


@dataclass(frozen=True)
class GenerationRequest:
    """One deterministic generation request (inert Data).

    ``mode`` is an informational case label (``t2v``/``t2i``/``i2v``/``t2v_audio``/``hard``);
    adapter behavior is driven only by the explicit fields below (so ``mode`` is never a hidden
    decision variable). The fixed params mirror the frozen determinism contract (INV-10).
    """

    mode: str
    case_id: str = ""
    prompt: str | None = None
    negative_prompt: str | None = None
    image_path: str | None = None
    generate_sound: bool = False
    # Fixed deterministic params (INV-10) — identical across every oracle/engine comparison.
    seed: int = 123
    flow_shift: float = 10.0
    guidance_scale: float = 6.0
    num_frames: int = 1
    height: int = 480
    width: int = 480
    num_inference_steps: int = 8


@dataclass(frozen=True)
class EngineInfo:
    """What an engine *is*, with load-time **verified** facts (inert Data).

    ``precision`` is verified against the checkpoint's ``quantization_config.json`` at load
    (defeating a silent FP8-as-NVFP4 mislabel); the invariant fields carry the evidence.
    """

    engine: str
    precision: Precision
    checkpoint_dir: str
    n_quantized: int = 0
    granularity: str = ""
    recipe: str = ""


@dataclass(frozen=True)
class GenerationResult:
    """Outputs of one generation (inert Data the harness compares).

    ``latents`` are the transformer's final pre-VAE latents (CPU float32 — the M1 input);
    ``frames`` are decoded H×W×3 float[0,1] arrays (the M2 input); ``audio`` is optional muxed
    audio. ``info`` records the engine/precision that actually produced this result.
    """

    case_id: str
    latents: Any
    frames: list[Any] = field(default_factory=list)
    audio: Any | None = None
    vram_peak_bytes: int = 0
    info: EngineInfo | None = None


class EngineAdapter(ABC):
    """A generation engine the equivalence harness can drive (INV-3).

    Implementations own all GPU I/O behind this small surface. ``generate`` is the only Action;
    ``info`` is read-only verified metadata. The harness never inspects engine internals — it
    compares two ``GenerationResult``s to a band verdict.
    """

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Run one deterministic generation under ``request``'s fixed params. Action (GPU I/O)."""

    @property
    @abstractmethod
    def info(self) -> EngineInfo:
        """The verified engine/precision metadata for results this adapter produces."""
