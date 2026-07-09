"""Unit tests for single-checkpoint label resolution (spec: single-checkpoint-serving — "A request
checkpoint label is optional and validated against the deployment", INV-2)."""
from __future__ import annotations

import pytest

from app.routes.checkpoint import deployed_checkpoint, resolve_checkpoint
from preprocessing.media import MediaValidationFailed


def test_absent_label_uses_deployed(monkeypatch):
    monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", "fp8")
    assert resolve_checkpoint(None) == "fp8"
    assert resolve_checkpoint("") == "fp8"


def test_matching_label_is_accepted(monkeypatch):
    monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", "fp8")
    assert resolve_checkpoint("fp8") == "fp8"


def test_mismatched_label_is_rejected(monkeypatch):
    monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", "fp8")
    with pytest.raises(MediaValidationFailed):
        resolve_checkpoint("nvfp4")


def test_nonlabel_value_is_rejected(monkeypatch):
    monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", "fp8")
    for bad in ("/data/models/Cosmos3-Nano", "../etc/passwd", "http://evil/x", "fp8; rm -rf"):
        with pytest.raises(MediaValidationFailed):
            resolve_checkpoint(bad)


def test_nvfp4_deployment_accepts_nvfp4_rejects_fp8(monkeypatch):
    monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", "nvfp4")
    assert deployed_checkpoint() == "nvfp4"
    assert resolve_checkpoint(None) == "nvfp4"
    assert resolve_checkpoint("nvfp4") == "nvfp4"
    with pytest.raises(MediaValidationFailed):
        resolve_checkpoint("fp8")


def test_default_deployment_is_fp8(monkeypatch):
    monkeypatch.delenv("COSMOS3_CHECKPOINT_LABEL", raising=False)
    assert deployed_checkpoint() == "fp8"
    assert resolve_checkpoint(None) == "fp8"
