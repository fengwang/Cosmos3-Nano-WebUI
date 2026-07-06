"""Modality validators + decode-safe header probes (ACD: pure Calculations + thin Actions; INV-6).

The validators (`validate_image|video|audio`, `validate_resolution|num_frames`) are **pure** over a
probed-metadata value and the limits — host-testable with synthetic inputs, returning ``None`` (Ok)
or a typed `MediaValidationError(code)` the edge maps to 413/415/422 (errors-as-data; only the shell
raises `MediaValidationFailed`). The `sniff_mime` + `probe_*` Actions are **stdlib-only** (no pillow /
no ffmpeg — the server core stays light) and **decode-safe**: they read magic bytes + header fields,
never fully decoding an untrusted payload (RK-11). MIME is authoritative from the **sniff**, not the
client's declared type. Refs: session_6/specs/modality-preprocessing.md; evidence_map A4/H4.
"""
from __future__ import annotations

import io
import struct
import wave
from dataclasses import dataclass
from enum import Enum

from preprocessing.limits import MediaLimits

IMAGE_MIMES = frozenset({"image/png", "image/jpeg", "image/webp"})
VIDEO_MIMES = frozenset({"video/mp4", "video/webm"})
AUDIO_MIMES = frozenset({"audio/wav", "audio/x-wav", "audio/flac"})

# JPEG Start-Of-Frame markers carrying the frame dimensions (exclude DHT/DAC/RSTn).
_JPEG_SOF = frozenset(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC}


class MediaErrorCode(Enum):
    """Why an upload/param is rejected — each maps to a fixed HTTP status (no string blindness)."""

    PAYLOAD_TOO_LARGE = "payload_too_large"          # → 413
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"  # → 415
    INVALID_DIMENSION = "invalid_dimension"          # → 422
    INVALID_PARAM = "invalid_param"                  # → 422


@dataclass(frozen=True)
class ProbedMedia:
    """The header-probed facts a validator needs (inert Data). Unknown fields are ``None``."""

    modality: str
    size_bytes: int
    mime: str | None = None
    width: int | None = None
    height: int | None = None
    frames: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    duration_s: float | None = None


@dataclass(frozen=True)
class MediaValidationError:
    """A structured, mappable rejection (no boolean/null blindness)."""

    code: MediaErrorCode
    message: str
    expected: int | str | None = None
    got: int | str | None = None


class MediaValidationFailed(Exception):
    """Raised by the Action shell to halt dispatch; carries the typed error (the pure validators never raise)."""

    def __init__(self, error: MediaValidationError) -> None:
        self.error = error
        super().__init__(f"{error.code.value}: {error.message}")


# ---- pure validators (errors-as-data) -------------------------------------------------------
def validate_image(meta: ProbedMedia, limits: MediaLimits) -> MediaValidationError | None:
    """Pure: size (413) → mime (415) → dimensions (422). ``None`` == Ok."""
    if meta.size_bytes > limits.max_image_bytes:
        return MediaValidationError(
            MediaErrorCode.PAYLOAD_TOO_LARGE, "image exceeds the byte cap",
            expected=limits.max_image_bytes, got=meta.size_bytes,
        )
    if meta.mime not in IMAGE_MIMES:
        return MediaValidationError(
            MediaErrorCode.UNSUPPORTED_MEDIA_TYPE, f"image mime {meta.mime!r} not in {sorted(IMAGE_MIMES)}",
        )
    if meta.width is not None and meta.height is not None:
        if min(meta.width, meta.height) <= 0 or max(meta.width, meta.height) > limits.max_image_dimension:
            return MediaValidationError(
                MediaErrorCode.INVALID_DIMENSION,
                f"image dimensions {meta.width}x{meta.height} outside (0, {limits.max_image_dimension}]",
                expected=limits.max_image_dimension, got=max(meta.width, meta.height),
            )
    return None


def validate_video(meta: ProbedMedia, limits: MediaLimits) -> MediaValidationError | None:
    """Pure: size (413) → mime (415) → frame/dimension caps (422) when probed. ``None`` == Ok."""
    if meta.size_bytes > limits.max_video_bytes:
        return MediaValidationError(
            MediaErrorCode.PAYLOAD_TOO_LARGE, "video exceeds the byte cap",
            expected=limits.max_video_bytes, got=meta.size_bytes,
        )
    if meta.mime not in VIDEO_MIMES:
        return MediaValidationError(
            MediaErrorCode.UNSUPPORTED_MEDIA_TYPE, f"video mime {meta.mime!r} not in {sorted(VIDEO_MIMES)}",
        )
    if meta.frames is not None and (meta.frames <= 0 or meta.frames > limits.max_num_frames):
        return MediaValidationError(
            MediaErrorCode.INVALID_PARAM, f"video frames {meta.frames} outside (0, {limits.max_num_frames}]",
            expected=limits.max_num_frames, got=meta.frames,
        )
    if (meta.width or meta.height) and max(meta.width or 0, meta.height or 0) > limits.max_image_dimension:
        return MediaValidationError(
            MediaErrorCode.INVALID_DIMENSION, "video frame dimension exceeds the cap",
            expected=limits.max_image_dimension, got=max(meta.width or 0, meta.height or 0),
        )
    return None


def validate_audio(meta: ProbedMedia, limits: MediaLimits) -> MediaValidationError | None:
    """Pure: size (413) → mime (415) → sample-rate/channels/duration (422). ``None`` == Ok."""
    if meta.size_bytes > limits.max_audio_bytes:
        return MediaValidationError(
            MediaErrorCode.PAYLOAD_TOO_LARGE, "audio exceeds the byte cap",
            expected=limits.max_audio_bytes, got=meta.size_bytes,
        )
    if meta.mime not in AUDIO_MIMES:
        return MediaValidationError(
            MediaErrorCode.UNSUPPORTED_MEDIA_TYPE, f"audio mime {meta.mime!r} not in {sorted(AUDIO_MIMES)}",
        )
    if meta.sample_rate is not None and meta.sample_rate != limits.audio_sample_rate:
        return MediaValidationError(
            MediaErrorCode.INVALID_PARAM, f"audio sample_rate must be {limits.audio_sample_rate} Hz",
            expected=limits.audio_sample_rate, got=meta.sample_rate,
        )
    if meta.channels is not None and meta.channels != limits.audio_channels:
        return MediaValidationError(
            MediaErrorCode.INVALID_PARAM, f"audio must have {limits.audio_channels} channels",
            expected=limits.audio_channels, got=meta.channels,
        )
    if meta.duration_s is not None and meta.duration_s > limits.max_audio_seconds:
        return MediaValidationError(
            MediaErrorCode.INVALID_PARAM, f"audio longer than {limits.max_audio_seconds}s",
        )
    return None


def validate_resolution(value: int, limits: MediaLimits) -> MediaValidationError | None:
    """Pure: a requested OUTPUT resolution must be a config-grounded family member (else 422)."""
    if value not in limits.resolutions:
        return MediaValidationError(
            MediaErrorCode.INVALID_DIMENSION, f"resolution {value} not in {sorted(limits.resolutions)}",
            expected=str(sorted(limits.resolutions)), got=value,
        )
    return None


def validate_dimension(value: int, limits: MediaLimits) -> MediaValidationError | None:
    """Pure: a requested OUTPUT height/width must be in the valid-dimensions set (else 422)."""
    if value not in limits.valid_dimensions:
        return MediaValidationError(
            MediaErrorCode.INVALID_DIMENSION, f"dimension {value} not in {sorted(limits.valid_dimensions)}",
            expected=str(sorted(limits.valid_dimensions)), got=value,
        )
    return None


def validate_num_frames(value: int, limits: MediaLimits) -> MediaValidationError | None:
    """Pure: a requested OUTPUT frame count must be in (0, max_num_frames] (RK-08 OOM guard; else 422)."""
    if value <= 0 or value > limits.max_num_frames:
        return MediaValidationError(
            MediaErrorCode.INVALID_PARAM, f"num_frames {value} outside (0, {limits.max_num_frames}]",
            expected=limits.max_num_frames, got=value,
        )
    return None


# ---- decode-safe header probes (stdlib-only Actions; never fully decode untrusted bytes) -----
def sniff_mime(data: bytes) -> str | None:
    """Calculation over the leading bytes: the magic-byte MIME, or ``None`` if unrecognized."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "audio/wav"
    if data[:4] == b"fLaC":
        return "audio/flac"
    if data[4:8] == b"ftyp":
        return "video/mp4"
    if data[:4] == b"\x1aE\xdf\xa3":
        return "video/webm"
    return None


def _png_dims(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 24 and data[12:16] == b"IHDR":
        return struct.unpack(">II", data[16:24])
    return None


def _jpeg_dims(data: bytes) -> tuple[int, int] | None:
    i, n = 2, len(data)
    while i + 9 < n:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker == 0xD8 or marker == 0xD9 or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg_len = int.from_bytes(data[i + 2:i + 4], "big")
        if marker in _JPEG_SOF:
            height = int.from_bytes(data[i + 5:i + 7], "big")
            width = int.from_bytes(data[i + 7:i + 9], "big")
            return width, height
        i += 2 + seg_len
    return None


def _image_dims(data: bytes, mime: str) -> tuple[int, int] | None:
    """Decode-safe dimension extraction from the header (no pixel decode). ``None`` if undetermined."""
    try:
        if mime == "image/png":
            return _png_dims(data)
        if mime == "image/jpeg":
            return _jpeg_dims(data)
    except (struct.error, IndexError, ValueError):
        return None
    return None  # image/webp: dimensions left unprobed (validated on size+mime); documented v1 gap


def probe_image(data: bytes) -> ProbedMedia:
    """Action: size + sniffed MIME (authoritative) + header dimensions. Never fully decodes the payload."""
    mime = sniff_mime(data)
    width = height = None
    if mime in IMAGE_MIMES:
        dims = _image_dims(data, mime)
        if dims is not None:
            width, height = dims
    return ProbedMedia(modality="image", size_bytes=len(data), mime=mime, width=width, height=height)


def probe_audio(data: bytes) -> ProbedMedia:
    """Action: size + sniffed MIME + (for WAV) stdlib `wave` header (sample_rate/channels/duration)."""
    mime = sniff_mime(data)
    sample_rate = channels = None
    duration_s: float | None = None
    if mime == "audio/wav":
        try:
            with wave.open(io.BytesIO(data), "rb") as handle:
                sample_rate = handle.getframerate()
                channels = handle.getnchannels()
                duration_s = handle.getnframes() / float(sample_rate) if sample_rate else None
        except (wave.Error, EOFError, struct.error):
            pass
    return ProbedMedia(
        modality="audio", size_bytes=len(data), mime=mime,
        sample_rate=sample_rate, channels=channels, duration_s=duration_s,
    )


def probe_video(data: bytes) -> ProbedMedia:
    """Action: size + sniffed MIME (frame/dimension probing needs ffmpeg → left to S7/the engine)."""
    return ProbedMedia(modality="video", size_bytes=len(data), mime=sniff_mime(data))
