"""Config-grounded media limits (ACD: inert Data + one env Action; INV-6).

The public caps are grounded in the model config (evidence_map A4): generation output resolution
families {256, 480, 720}; conditioning/sound audio 48 kHz stereo; plus conservative byte / frame /
duration / dimension caps that bound the untiled-VAE decode peak (RK-08) and decode-bomb uploads
(RK-11). These are the INV-6 public contract — not engine internals — and the operator can tighten
them via the environment without a code change. Refs: session_6/specs/modality-preprocessing.md.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

MiB = 1024 * 1024


@dataclass(frozen=True)
class MediaLimits:
    """The public modality caps (inert Data)."""

    # Generation OUTPUT params (the RK-08 OOM guard lives here, not on the uploaded conditioning media).
    resolutions: frozenset[int] = frozenset({256, 480, 720})
    valid_dimensions: frozenset[int] = frozenset({256, 480, 640, 720, 960, 1280})
    max_num_frames: int = 720
    # Conditioning/sound AUDIO (must match the model's 48 kHz stereo tokenizer — A4).
    audio_sample_rate: int = 48000
    audio_channels: int = 2
    max_audio_seconds: float = 60.0
    # Upload byte caps (→ 413) + an uploaded-image dimension cap (decode-bomb guard, RK-11).
    max_image_bytes: int = 32 * MiB
    max_video_bytes: int = 512 * MiB
    max_audio_bytes: int = 64 * MiB
    max_image_dimension: int = 4096

    @staticmethod
    def from_env() -> "MediaLimits":
        """Action: read operator overrides; unset values keep the grounded defaults."""
        d = MediaLimits()
        return MediaLimits(
            resolutions=d.resolutions,
            max_num_frames=int(os.environ.get("COSMOS3_MAX_NUM_FRAMES", str(d.max_num_frames))),
            audio_sample_rate=int(os.environ.get("COSMOS3_AUDIO_SAMPLE_RATE", str(d.audio_sample_rate))),
            audio_channels=int(os.environ.get("COSMOS3_AUDIO_CHANNELS", str(d.audio_channels))),
            max_audio_seconds=float(os.environ.get("COSMOS3_MAX_AUDIO_SECONDS", str(d.max_audio_seconds))),
            max_image_bytes=int(os.environ.get("COSMOS3_MAX_IMAGE_BYTES", str(d.max_image_bytes))),
            max_video_bytes=int(os.environ.get("COSMOS3_MAX_VIDEO_BYTES", str(d.max_video_bytes))),
            max_audio_bytes=int(os.environ.get("COSMOS3_MAX_AUDIO_BYTES", str(d.max_audio_bytes))),
            max_image_dimension=int(os.environ.get("COSMOS3_MAX_IMAGE_DIMENSION", str(d.max_image_dimension))),
        )
