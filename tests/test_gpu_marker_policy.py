"""Regression tests for the GPU-marker collection guard in ``tests/conftest.py``.

No `@pytest.mark.gpu` test exists in the imported CPU-safe suite yet, so without
these the guard (a core deliverable of the ``gpu_test_isolation`` capability) would
have zero committed coverage. We load the sibling ``conftest.py`` by explicit path
(avoiding the prepend-mode ``conftest`` name ambiguity) and exercise both the
truthy env parsing and the collection hook against fake items.
"""

import importlib.util
from pathlib import Path

_CONFTEST_PATH = Path(__file__).with_name("conftest.py")
_spec = importlib.util.spec_from_file_location("_s5_root_conftest", _CONFTEST_PATH)
assert _spec is not None and _spec.loader is not None, f"cannot load {_CONFTEST_PATH}"
conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(conftest)


class _FakeItem:
    """Minimal stand-in for a pytest ``Item`` (keywords membership + add_marker)."""

    def __init__(self, keywords):
        self.keywords = set(keywords)
        self.markers = []

    def add_marker(self, marker):
        self.markers.append(marker)


def test_gpu_enabled_truthy_parsing(monkeypatch):
    for val in ["1", "true", "TRUE", "yes", "on", " 1 "]:
        monkeypatch.setenv("COSMOS3_ENABLE_GPU_TESTS", val)
        assert conftest._gpu_enabled() is True, val
    for val in ["", "0", "false", "no", "off", "maybe"]:
        monkeypatch.setenv("COSMOS3_ENABLE_GPU_TESTS", val)
        assert conftest._gpu_enabled() is False, val
    monkeypatch.delenv("COSMOS3_ENABLE_GPU_TESTS", raising=False)
    assert conftest._gpu_enabled() is False


def test_gpu_item_skipped_when_opt_in_unset(monkeypatch):
    monkeypatch.delenv("COSMOS3_ENABLE_GPU_TESTS", raising=False)
    gpu_item = _FakeItem({"gpu"})
    cpu_item = _FakeItem({"unit"})
    conftest.pytest_collection_modifyitems([gpu_item, cpu_item])
    assert len(gpu_item.markers) == 1
    assert gpu_item.markers[0].name == "skip"
    assert "COSMOS3_ENABLE_GPU_TESTS" in gpu_item.markers[0].kwargs["reason"]
    assert cpu_item.markers == []  # non-gpu tests are never touched


def test_gpu_item_runs_when_opted_in(monkeypatch):
    monkeypatch.setenv("COSMOS3_ENABLE_GPU_TESTS", "1")
    gpu_item = _FakeItem({"gpu"})
    conftest.pytest_collection_modifyitems([gpu_item])
    assert gpu_item.markers == []  # opted in -> not skipped
