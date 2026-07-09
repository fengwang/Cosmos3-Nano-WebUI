"""Scaffolding: the new S6 packages import torch-free (the host-loop guarantee).

Reaching here in the torch-free host venv proves `orchestrator`, `jobs`, and `preprocessing`
(and their pure submodules) import with no heavy ML dependency at module scope.
"""
from __future__ import annotations

import sys


def test_s6_packages_import_torch_free():
    import jobs  # noqa: F401
    import orchestrator  # noqa: F401
    import preprocessing  # noqa: F401
    from preprocessing import limits, media, paths  # noqa: F401

    assert "torch" not in sys.modules
