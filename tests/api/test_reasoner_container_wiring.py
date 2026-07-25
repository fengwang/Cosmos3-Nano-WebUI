"""AM-S2: reasoning is served by a separate vllm-reasoner CONTAINER plane (zero-BF16 FP8, off the
quantized understanding tower), not an in-api subprocess. These tests pin the *app-wired* container
path — the contract's adversarial case warns that a stub reasoner must never stand in for the real
quantized wiring. Host-testable: building the spec/stream has no side effects (no docker, no GPU).
"""
from __future__ import annotations

import json

from orchestrator.planes import Plane, ProbeKind, container_reasoning_spec


def test_container_reasoning_spec_is_reasoning_http_probe():
    spec = container_reasoning_spec(base_url="http://vllm-reasoner:8000")
    assert spec.plane is Plane.REASONING
    assert spec.argv == ()                      # docker-managed; no subprocess argv (not vllm serve in-api)
    assert spec.probe_kind is ProbeKind.HTTP
    assert spec.probe_target == "http://vllm-reasoner:8000/v1/models"
    assert spec.strip_parent_env is False       # no in-api venv to isolate (that was the subprocess path)


def test_container_reasoning_spec_trims_trailing_slash():
    spec = container_reasoning_spec(base_url="http://vllm-reasoner:8000/")
    assert spec.probe_target == "http://vllm-reasoner:8000/v1/models"


def test_vllm_reasoner_stream_targets_container_url(monkeypatch):
    """VllmReasonerStream must POST to the reasoner CONTAINER's OpenAI endpoint (env-configured base
    URL), model `cosmos3-reasoner`, streaming — NOT the old 127.0.0.1:8765 subprocess."""
    monkeypatch.setenv("COSMOS3_VLLM_REASONER_URL", "http://vllm-reasoner:8000")
    from app.routes.reasoning import VllmReasonerStream

    captured: dict = {}

    class _Resp:
        def __enter__(self):
            return iter([b"data: [DONE]\n"])

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _Resp()

    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    stream = VllmReasonerStream()
    list(stream.stream({"prompt": "hi", "max_tokens": 8, "image_path": None, "video_path": None}))

    assert captured["url"] == "http://vllm-reasoner:8000/v1/chat/completions"
    assert captured["body"]["model"] == "cosmos3-reasoner"
    assert captured["body"]["stream"] is True
    assert captured["body"]["max_tokens"] == 8


def test_vllm_reasoner_stream_default_base_url(monkeypatch):
    monkeypatch.delenv("COSMOS3_VLLM_REASONER_URL", raising=False)
    from app.routes.reasoning import VllmReasonerStream

    assert VllmReasonerStream()._base_url == "http://vllm-reasoner:8000"
