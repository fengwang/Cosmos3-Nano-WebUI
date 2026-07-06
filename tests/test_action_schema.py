"""Host (torch-free) tests for the embodiment-schema validator.

One test per scenario in docs/session_4/specs/embodiment-schema-validator.md. The validator is a pure
Calculation: validate(spec) -> None (Ok) | ActionValidationError. EC-A4 (width-10 -> av) is the permanent
negative regression and MUST reject BEFORE any engine dispatch (INV-6 / RK-12). The 16-400 window governs
chunk_size (the action sequence length) — see session_4/failure_arbiter.md FA-1.
"""
from __future__ import annotations

from preprocessing.action_schema import (
    ActionMode,
    ActionSpec,
    ActionValidationError,
    ErrorCode,
    raw_action_dim_of,
    validate,
)


def _fd(
    domain: str = "av",
    width: int | None = 9,
    chunk: int = 16,
    has_image: bool = True,
    has_video: bool = False,
    tier: int = 480,
) -> ActionSpec:
    """A valid forward-dynamics spec, overridable per test."""
    return ActionSpec(
        mode=ActionMode.FORWARD_DYNAMICS,
        domain_name=domain,
        chunk_size=chunk,
        raw_action_width=width,
        resolution_tier=tier,
        has_image=has_image,
        has_video=has_video,
    )


def test_ec_a4_width10_to_av_rejected():
    """EC-A4: a width-10 raw_actions tensor for the 9-D `av` embodiment is rejected (WIDTH_MISMATCH)."""
    err = validate(_fd(domain="av", width=10))
    assert isinstance(err, ActionValidationError)
    assert err.code is ErrorCode.WIDTH_MISMATCH
    assert err.expected == 9 and err.got == 10
    assert "av" in err.message


def test_correct_width_passes():
    assert validate(_fd(domain="av", width=9)) is None


def test_raw_action_dim_lookup():
    assert raw_action_dim_of("av") == 9
    assert raw_action_dim_of("agibotworld") == 29
    assert raw_action_dim_of("hand_pose") == 57
    assert raw_action_dim_of("no_action") is None


def test_unknown_embodiment_rejected():
    err = validate(_fd(domain="frobnicator", width=9))
    assert isinstance(err, ActionValidationError) and err.code is ErrorCode.UNKNOWN_EMBODIMENT


def test_unsupported_for_inference_rejected():
    for dom in ("no_action", "libero"):
        err = validate(_fd(domain=dom, width=9))
        assert isinstance(err, ActionValidationError)
        assert err.code is ErrorCode.UNSUPPORTED_FOR_INFERENCE


def test_chunk_window_below_rejected():
    err = validate(_fd(chunk=8))  # >=1 but < 16
    assert isinstance(err, ActionValidationError) and err.code is ErrorCode.FRAME_WINDOW


def test_chunk_window_above_rejected():
    err = validate(_fd(chunk=512))
    assert isinstance(err, ActionValidationError) and err.code is ErrorCode.FRAME_WINDOW


def test_chunk_window_bounds_inclusive():
    assert validate(_fd(chunk=16)) is None
    assert validate(_fd(chunk=400)) is None


def test_chunk_size_zero_rejected():
    err = validate(_fd(chunk=0))  # < 1 -> BAD_CHUNK (engine minimum), checked before the window
    assert isinstance(err, ActionValidationError) and err.code is ErrorCode.BAD_CHUNK


def test_bad_resolution_tier_rejected():
    err = validate(_fd(tier=999))
    assert isinstance(err, ActionValidationError) and err.code is ErrorCode.BAD_RESOLUTION_TIER
    assert err.got == 999


def test_valid_resolution_tiers_pass():
    for tier in (256, 480, 704, 720):
        assert validate(_fd(tier=tier)) is None


def test_inverse_dynamics_requires_video():
    spec = ActionSpec(
        mode=ActionMode.INVERSE_DYNAMICS, domain_name="av", chunk_size=16,
        raw_action_width=None, has_image=False, has_video=False,
    )
    err = validate(spec)
    assert isinstance(err, ActionValidationError) and err.code is ErrorCode.CONDITION_MISSING


def test_inverse_dynamics_with_video_passes():
    spec = ActionSpec(
        mode=ActionMode.INVERSE_DYNAMICS, domain_name="av", chunk_size=16,
        raw_action_width=None, has_image=False, has_video=True,
    )
    assert validate(spec) is None


def test_image_and_video_conflict_rejected():
    err = validate(_fd(has_image=True, has_video=True))
    assert isinstance(err, ActionValidationError) and err.code is ErrorCode.CONDITION_CONFLICT


def test_forward_dynamics_without_actions_rejected():
    err = validate(_fd(width=None))
    assert isinstance(err, ActionValidationError) and err.code is ErrorCode.CONDITION_MISSING


def test_policy_requires_image():
    spec = ActionSpec(
        mode=ActionMode.POLICY, domain_name="agibotworld", chunk_size=16,
        raw_action_width=None, has_image=False, has_video=False,
    )
    err = validate(spec)
    assert isinstance(err, ActionValidationError) and err.code is ErrorCode.CONDITION_MISSING


def test_policy_with_image_passes():
    spec = ActionSpec(
        mode=ActionMode.POLICY, domain_name="agibotworld", chunk_size=16,
        raw_action_width=None, has_image=True, has_video=False,
    )
    assert validate(spec) is None
