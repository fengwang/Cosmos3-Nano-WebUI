"""Spec: modality-preprocessing — pure validators (413/415/422), sniffer, decode-safe image probe.

The validators are pure over a probed-metadata value (no I/O), so every scenario is host-runnable
with synthetic ``ProbedMedia``. The sniffer + image-header parser are stdlib-only (no pillow/ffmpeg)
and decode-safe (header bytes only). Covers EC-S3 (413/415/422, no decoder crash).
"""
from __future__ import annotations

import struct

from preprocessing.limits import MediaLimits
from preprocessing.media import (
    MediaErrorCode,
    MediaValidationFailed,
    ProbedMedia,
    probe_image,
    sniff_mime,
    validate_audio,
    validate_image,
    validate_num_frames,
    validate_resolution,
    validate_video,
)

LIM = MediaLimits()


def _png_bytes(width: int, height: int) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00"
    chunk = struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr + b"\x00\x00\x00\x00"
    return sig + chunk


# ---- image ----------------------------------------------------------------------------------
def test_image_oversized_is_413():
    meta = ProbedMedia(modality="image", size_bytes=LIM.max_image_bytes + 1, mime="image/png", width=64, height=64)
    err = validate_image(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.PAYLOAD_TOO_LARGE


def test_image_wrong_mime_is_415():
    meta = ProbedMedia(modality="image", size_bytes=100, mime="text/plain", width=64, height=64)
    err = validate_image(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.UNSUPPORTED_MEDIA_TYPE


def test_image_over_dimension_is_422():
    meta = ProbedMedia(modality="image", size_bytes=100, mime="image/png", width=LIM.max_image_dimension + 1, height=64)
    err = validate_image(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.INVALID_DIMENSION


def test_image_valid_passes():
    meta = ProbedMedia(modality="image", size_bytes=100, mime="image/jpeg", width=480, height=480)
    assert validate_image(meta, LIM) is None


# ---- video ----------------------------------------------------------------------------------
def test_video_oversized_is_413():
    meta = ProbedMedia(modality="video", size_bytes=LIM.max_video_bytes + 1, mime="video/mp4")
    err = validate_video(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.PAYLOAD_TOO_LARGE


def test_video_wrong_mime_is_415():
    meta = ProbedMedia(modality="video", size_bytes=100, mime="application/zip")
    err = validate_video(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.UNSUPPORTED_MEDIA_TYPE


def test_video_valid_passes():
    meta = ProbedMedia(modality="video", size_bytes=100, mime="video/mp4")
    assert validate_video(meta, LIM) is None


# ---- audio ----------------------------------------------------------------------------------
def test_audio_wrong_sample_rate_is_422():
    meta = ProbedMedia(modality="audio", size_bytes=100, mime="audio/wav", sample_rate=44100, channels=2, duration_s=1.0)
    err = validate_audio(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.INVALID_PARAM


def test_audio_wrong_channels_is_422():
    meta = ProbedMedia(modality="audio", size_bytes=100, mime="audio/wav", sample_rate=48000, channels=1, duration_s=1.0)
    err = validate_audio(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.INVALID_PARAM


def test_audio_over_duration_is_422():
    meta = ProbedMedia(
        modality="audio", size_bytes=100, mime="audio/wav", sample_rate=48000, channels=2,
        duration_s=LIM.max_audio_seconds + 1,
    )
    err = validate_audio(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.INVALID_PARAM


def test_audio_valid_passes():
    meta = ProbedMedia(modality="audio", size_bytes=100, mime="audio/wav", sample_rate=48000, channels=2, duration_s=2.0)
    assert validate_audio(meta, LIM) is None


# ---- output param checks --------------------------------------------------------------------
def test_resolution_param_in_family_passes_else_422():
    assert validate_resolution(480, LIM) is None
    err = validate_resolution(123, LIM)
    assert err is not None and err.code is MediaErrorCode.INVALID_DIMENSION


def test_num_frames_param_capped():
    assert validate_num_frames(48, LIM) is None
    err = validate_num_frames(LIM.max_num_frames + 1, LIM)
    assert err is not None and err.code is MediaErrorCode.INVALID_PARAM
    err0 = validate_num_frames(0, LIM)
    assert err0 is not None and err0.code is MediaErrorCode.INVALID_PARAM


# ---- sniffer + decode-safe image probe ------------------------------------------------------
def test_sniff_mime_recognizes_png_and_rejects_garbage():
    assert sniff_mime(_png_bytes(8, 8)) == "image/png"
    assert sniff_mime(b"\xff\xd8\xff\xe0\x00\x10JFIF") == "image/jpeg"
    assert sniff_mime(b"not a real media file") is None


def test_probe_image_reads_dimensions_from_header():
    meta = probe_image(_png_bytes(640, 360))
    assert meta.mime == "image/png" and meta.width == 640 and meta.height == 360
    assert meta.size_bytes == len(_png_bytes(640, 360))


def test_probe_image_on_malformed_does_not_crash_and_flags_415():
    # decode-safety: malformed bytes are not fully decoded; mime sniff fails → validator 415
    meta = probe_image(b"definitely not an image")
    assert meta.mime is None  # sniff failed; declared mime is not trusted blindly
    err = validate_image(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.UNSUPPORTED_MEDIA_TYPE


def test_probe_image_oversize_can_be_caught_before_dimension_parse():
    # a huge declared size short-circuits to 413 without needing a successful header parse
    meta = ProbedMedia(modality="image", size_bytes=LIM.max_image_bytes + 1, mime=None, width=None, height=None)
    err = validate_image(meta, LIM)
    assert err is not None and err.code is MediaErrorCode.PAYLOAD_TOO_LARGE


def test_media_validation_failed_carries_error():
    meta = ProbedMedia(modality="image", size_bytes=1, mime="text/plain")
    err = validate_image(meta, LIM)
    exc = MediaValidationFailed(err)
    assert exc.error.code is MediaErrorCode.UNSUPPORTED_MEDIA_TYPE
