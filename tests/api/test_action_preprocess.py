"""Spec: modality-preprocessing — action requests reuse the S4 embodiment validator (EC-A4).

S6 does not re-implement embodiment validation; it reuses `preprocessing.action_schema.validate`
unchanged. This anchors the dependency the S6 API edge relies on: a width/embodiment mismatch is a
typed error the router maps to 422 BEFORE any orchestrator/engine dispatch (RK-12).
"""
from __future__ import annotations

from preprocessing.action_schema import (
    ActionMode,
    ActionSpec,
    ErrorCode,
    validate,
)


def test_ec_a4_width_mismatch_is_rejected():
    # EC-A4: a 10-D tensor sent to the 9-D `av` embodiment → WIDTH_MISMATCH (→ 422, never dispatched)
    spec = ActionSpec(
        mode=ActionMode.FORWARD_DYNAMICS, domain_name="av", chunk_size=32,
        raw_action_width=10, has_image=True,
    )
    err = validate(spec)
    assert err is not None and err.code is ErrorCode.WIDTH_MISMATCH
    assert err.expected == 9 and err.got == 10


def test_valid_action_spec_passes():
    spec = ActionSpec(
        mode=ActionMode.FORWARD_DYNAMICS, domain_name="av", chunk_size=32,
        raw_action_width=9, has_image=True,
    )
    assert validate(spec) is None
