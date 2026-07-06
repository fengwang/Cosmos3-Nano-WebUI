"""Boundary translation: adapter internal names ↔ diffusers pipeline names for audio.

The diffusers Cosmos3OmniPipeline uses ``enable_sound`` (parameter) and ``out.sound`` (output),
while our internal API uses ``generate_sound`` (GenerationRequest) and ``.audio`` (GenerationResult).
The adapter translates at the boundary. These tests verify that translation.

Spec: session_3/specs/audio-wiring.md, session_3/specs/audio-boundary-test.md.
"""
from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Stub torch before importing the adapter (its module-level imports are torch-free,
# but we need torch in sys.modules for the deferred imports inside generate()).
_torch = MagicMock()
_torch.float32 = "float32"
_torch.bfloat16 = "bfloat16"
_torch.empty.return_value = MagicMock()
_torch.Generator.return_value.manual_seed.return_value = MagicMock()
_torch.cuda.max_memory_allocated.return_value = 1024
_torch.autocast.return_value.__enter__ = MagicMock(return_value=None)
_torch.autocast.return_value.__exit__ = MagicMock(return_value=False)

_np = MagicMock()
_pil = MagicMock()


@pytest.fixture(autouse=True)
def _stub_gpu_modules(monkeypatch):
    """Inject GPU stubs and bypass seed_everything / _frames_to_float."""
    monkeypatch.setitem(sys.modules, "torch", _torch)
    monkeypatch.setitem(sys.modules, "numpy", _np)
    monkeypatch.setitem(sys.modules, "PIL", _pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", _pil.Image)

    from engines.diffusers_oracle import adapter

    monkeypatch.setattr(adapter, "seed_everything", lambda _seed: None)
    monkeypatch.setattr(adapter, "_frames_to_float", lambda v: list(v))


# noqa placement: this import is intentionally after the sys.modules stubs above.
from engines.base import EngineInfo, GenerationRequest, Precision  # noqa: E402


_INFO = EngineInfo("diffusers_oracle", Precision.NVFP4, "/model")
_SOUND_TENSOR = object()


class _PipeWithSound:
    """Mock pipeline whose __call__ accepts ``enable_sound``."""

    def __init__(self):
        self.last_call_kwargs: dict = {}

    def __call__(self, *, enable_sound=False, **kwargs):
        self.last_call_kwargs = {"enable_sound": enable_sound, **kwargs}
        sound = _SOUND_TENSOR if enable_sound else None
        return SimpleNamespace(video=["frame0"], sound=sound)


class _PipeWithoutSound:
    """Mock pipeline whose __call__ does NOT accept ``enable_sound``."""

    def __init__(self):
        self.last_call_kwargs: dict = {}

    def __call__(self, **kwargs):
        self.last_call_kwargs = dict(kwargs)
        return SimpleNamespace(video=["frame0"], sound=None)


def _make_adapter(pipe):
    from engines.diffusers_oracle.adapter import DiffusersOracleAdapter

    return DiffusersOracleAdapter(pipe, _INFO, device="cpu")


def _request(*, generate_sound: bool = False) -> GenerationRequest:
    return GenerationRequest(mode="t2v_audio" if generate_sound else "t2v",
                             prompt="test", generate_sound=generate_sound)


def test_enable_sound_passed_when_generate_sound_requested():
    pipe = _PipeWithSound()
    adapter = _make_adapter(pipe)
    adapter.generate(_request(generate_sound=True))
    assert pipe.last_call_kwargs["enable_sound"] is True


def test_enable_sound_not_passed_when_generate_sound_false():
    pipe = _PipeWithSound()
    adapter = _make_adapter(pipe)
    adapter.generate(_request(generate_sound=False))
    assert pipe.last_call_kwargs.get("enable_sound", False) is False


def test_enable_sound_omitted_when_pipeline_lacks_it():
    pipe = _PipeWithoutSound()
    adapter = _make_adapter(pipe)
    adapter.generate(_request(generate_sound=True))
    assert "enable_sound" not in pipe.last_call_kwargs


def test_sound_output_mapped_to_audio_result():
    pipe = _PipeWithSound()
    adapter = _make_adapter(pipe)
    result = adapter.generate(_request(generate_sound=True))
    assert result.audio is _SOUND_TENSOR


def test_none_audio_when_sound_not_requested():
    pipe = _PipeWithSound()
    adapter = _make_adapter(pipe)
    result = adapter.generate(_request(generate_sound=False))
    assert result.audio is None


def test_none_audio_when_pipeline_returns_no_sound():
    """Pipeline accepted enable_sound=True but returned sound=None (silent generation)."""

    class _PipeSilent(_PipeWithSound):
        def __call__(self, *, enable_sound=False, **kwargs):
            self.last_call_kwargs = {"enable_sound": enable_sound, **kwargs}
            return SimpleNamespace(video=["frame0"], sound=None)

    pipe = _PipeSilent()
    adapter = _make_adapter(pipe)
    result = adapter.generate(_request(generate_sound=True))
    assert pipe.last_call_kwargs["enable_sound"] is True
    assert result.audio is None
