"""endpoint_for resolver — the single deployed generation endpoint from operator env (INV-3/INV-8).

Spec: session_6/specs/single-checkpoint-serving.md. A standalone deployment serves one checkpoint, so
``endpoint_for()`` takes no label and returns the one container/URL; ``.checkpoint`` reflects the
deployed label (``COSMOS3_CHECKPOINT_LABEL``). Pure; no docker, no server.
"""
from __future__ import annotations

from engines.vllm_omni.endpoints import deployed_checkpoint, endpoint_for

_OMNI_ENV = ("COSMOS3_VLLM_OMNI_URL", "COSMOS3_GEN_CONTAINER", "COSMOS3_CHECKPOINT_LABEL")


def _clear(monkeypatch) -> None:
    for key in _OMNI_ENV:
        monkeypatch.delenv(key, raising=False)


def test_resolves_the_single_default_endpoint(monkeypatch):
    _clear(monkeypatch)
    ep = endpoint_for()
    assert ep.checkpoint == "fp8"  # default deployment
    assert ep.container == "cosmos3-nano-webui-vllm-omni"
    assert ep.base_url == "http://vllm-omni:8000"


def test_checkpoint_reflects_the_deployed_label(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", "nvfp4")
    assert deployed_checkpoint() == "nvfp4"
    ep = endpoint_for()  # still the single endpoint; only the reported label changes
    assert ep.checkpoint == "nvfp4"
    assert ep.container == "cosmos3-nano-webui-vllm-omni"
    assert ep.base_url == "http://vllm-omni:8000"


def test_env_overrides_are_honored(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("COSMOS3_VLLM_OMNI_URL", "http://fp:9000")
    monkeypatch.setenv("COSMOS3_GEN_CONTAINER", "fp-ctr")
    ep = endpoint_for()
    assert (ep.container, ep.base_url) == ("fp-ctr", "http://fp:9000")


def test_unknown_label_env_defaults_to_fp8(monkeypatch):
    # A misconfigured/empty label must not crash resolution — default to fp8 (the compose sets it).
    _clear(monkeypatch)
    monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", "bogus")
    assert deployed_checkpoint() == "fp8"
    assert endpoint_for().checkpoint == "fp8"
