"""Unit tests for gen_worker's IPC→GenerationRequest mapping (spec: video-resolution-default).

The dormant diffusers path must apply the same mode-aware 720p video default as the deployed
vLLM-Omni path, so a switch of COSMOS3_GEN_ENGINE does not change the shipped default resolution.
Torch-free: engines.base is imported deferred; no GPU.
"""
from __future__ import annotations

import pytest

from orchestrator.gen_worker import _to_generation_request


@pytest.mark.parametrize("mode", ["t2v", "i2v", "t2v_audio"])
def test_video_request_defaults_to_720p(mode):
    req = _to_generation_request({"mode": mode, "params": {}, "job_id": "j"})
    assert (req.width, req.height) == (1280, 720)


def test_t2i_request_dims_unchanged():
    req = _to_generation_request({"mode": "t2i", "params": {}, "job_id": "j"})
    assert (req.width, req.height) == (480, 480)


def test_explicit_dims_win():
    req = _to_generation_request({"mode": "t2v", "params": {"width": 640, "height": 480}, "job_id": "j"})
    assert (req.width, req.height) == (640, 480)


def test_explicit_square_resolution_wins():
    req = _to_generation_request({"mode": "t2v", "params": {"resolution": 480}, "job_id": "j"})
    assert (req.width, req.height) == (480, 480)
