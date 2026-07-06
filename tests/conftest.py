"""Root test policy for the CPU loop (Session 5).

GPU isolation
-------------
Tests marked ``@pytest.mark.gpu`` require the RTX 5090 and are **skipped on the
torch-free CPU loop** unless the opt-in env var ``COSMOS3_ENABLE_GPU_TESTS`` is
truthy. CI additionally passes ``-m "not gpu"`` — the two mechanisms are
independent, so neither an omitted CI flag nor a newly-added GPU test can let GPU
work run (or fail) in CPU CI.

Convention for future GPU tests
-------------------------------
A GPU-only test module MUST guard its heavy imports (for example
``torch = pytest.importorskip("torch")`` at module top, or import inside the test
body) so pytest can *import* the module during collection on a CPU runner without
the ``oracle`` extra. The ``gpu`` marker controls *execution*; it cannot prevent an
unguarded top-level ``import torch`` from breaking *collection*.

Manual GPU run (S8 release gate, not part of CPU CI)::

    COSMOS3_ENABLE_GPU_TESTS=1 pytest -m gpu
"""

import os

import pytest

_GPU_OPT_IN = "COSMOS3_ENABLE_GPU_TESTS"
_TRUTHY = {"1", "true", "yes", "on"}


def _gpu_enabled() -> bool:
    """Calculation: is the GPU opt-in set to a truthy value?"""
    return os.environ.get(_GPU_OPT_IN, "").strip().lower() in _TRUTHY


def pytest_collection_modifyitems(items):
    """Skip ``gpu``-marked items unless the GPU opt-in is enabled.

    pytest matches hook arguments by name, so declaring only ``items`` is valid.
    """
    if _gpu_enabled():
        return
    skip_gpu = pytest.mark.skip(
        reason=f"gpu test skipped on the CPU loop; set {_GPU_OPT_IN}=1 to run"
    )
    for item in items:
        if "gpu" in item.keywords:
            item.add_marker(skip_gpu)
