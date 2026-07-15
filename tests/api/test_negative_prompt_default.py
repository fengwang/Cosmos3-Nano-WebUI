"""Unit tests for the curated negative-prompt default loader (spec: negative-prompt-default).

Host-testable: pure path derivation + a cached file-loading Action with graceful fallback.
Covers EV-UX-NEGPROMPT-DEFAULT-APPLIED (loader half) and EV-UX-NEGPROMPT-NO-ABS-PATH.
"""
from __future__ import annotations

import inspect
import json
import logging

import pytest

from preprocessing import negative_prompt as np


@pytest.fixture(autouse=True)
def _clear_cache():
    """The loader caches by path; reset between tests so env/file changes take effect."""
    np._read_default.cache_clear()
    yield
    np._read_default.cache_clear()


def _write_asset(model_dir, text: str) -> None:
    assets = model_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "negative_prompt.json").write_text(text, encoding="utf-8")


# ── pure path derivation (INV-1) ─────────────────────────────────────────────

def test_negative_prompt_path_derives_from_model_dir():
    assert np.negative_prompt_path("/models/checkpoint") == "/models/checkpoint/assets/negative_prompt.json"


def test_loader_source_has_no_hardcoded_absolute_path():
    # EV-UX-NEGPROMPT-NO-ABS-PATH: the path derives from COSMOS3_MODEL_DIR, never a baked-in literal.
    assert "/data/models" not in inspect.getsource(np)


# ── loading + graceful degradation ───────────────────────────────────────────

def test_loads_verbatim_text_when_present(tmp_path, monkeypatch):
    text = '{\n  "subjects": [],\n  "background_setting": "flat"\n}'
    _write_asset(tmp_path, text)
    monkeypatch.setenv("COSMOS3_MODEL_DIR", str(tmp_path))
    loaded = np.load_default_negative_prompt()
    assert loaded == text                     # verbatim (serialized-JSON-string transport)
    assert json.loads(loaded)["background_setting"] == "flat"  # and it is valid JSON


def test_unset_model_dir_returns_none(monkeypatch):
    monkeypatch.delenv("COSMOS3_MODEL_DIR", raising=False)
    assert np.load_default_negative_prompt() is None


def test_missing_file_returns_none_and_logs_once(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("COSMOS3_MODEL_DIR", str(tmp_path))  # dir exists, asset does not
    with caplog.at_level(logging.WARNING, logger="cosmos3.preprocessing.negative_prompt"):
        assert np.load_default_negative_prompt() is None
        assert np.load_default_negative_prompt() is None  # second call is a cache hit
    warnings = [r for r in caplog.records if "negative-prompt default unavailable" in r.getMessage()]
    assert len(warnings) == 1  # graceful degradation, logged exactly once


def test_malformed_json_returns_none(tmp_path, monkeypatch):
    _write_asset(tmp_path, "{ this is not valid json ")
    monkeypatch.setenv("COSMOS3_MODEL_DIR", str(tmp_path))
    assert np.load_default_negative_prompt() is None  # validity gate → graceful None


def test_file_is_read_once_cached(tmp_path, monkeypatch):
    text = '{"subjects": []}'
    _write_asset(tmp_path, text)
    monkeypatch.setenv("COSMOS3_MODEL_DIR", str(tmp_path))
    first = np.load_default_negative_prompt()
    (tmp_path / "assets" / "negative_prompt.json").unlink()  # delete after first read
    second = np.load_default_negative_prompt()
    assert first == second == text  # cached: the deleted file was not re-read
