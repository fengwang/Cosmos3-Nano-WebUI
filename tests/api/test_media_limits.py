"""Spec: modality-preprocessing — config-grounded limits (evidence_map A4)."""
from __future__ import annotations

from preprocessing.limits import MediaLimits


def test_default_limits_are_config_grounded():
    lim = MediaLimits()
    assert lim.resolutions == frozenset({256, 480, 720})
    assert lim.audio_sample_rate == 48000
    assert lim.audio_channels == 2
    assert lim.max_image_bytes > 0
    assert lim.max_video_bytes > 0
    assert lim.max_audio_bytes > 0
    assert lim.max_num_frames > 0
    assert lim.max_audio_seconds > 0


def test_from_env_overrides(monkeypatch):
    monkeypatch.setenv("COSMOS3_MAX_IMAGE_BYTES", "1234")
    monkeypatch.setenv("COSMOS3_MAX_NUM_FRAMES", "17")
    lim = MediaLimits.from_env()
    assert lim.max_image_bytes == 1234
    assert lim.max_num_frames == 17
    # unset values keep the grounded defaults
    assert lim.resolutions == frozenset({256, 480, 720})
