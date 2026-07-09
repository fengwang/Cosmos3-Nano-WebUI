"""Embodiment-schema validator (ACD: Data + pure Calculations; torch-free).

The single public Calculation ``validate(spec)`` returns ``None`` (Ok) or a typed
``ActionValidationError`` that maps to a 422 **before** engine dispatch (INV-6 / RK-12). ``≤64`` (the
model's padded ``action_dim``) is necessary but NOT sufficient — the real check is the **exact
per-embodiment width**, so a width-10 tensor for the 9-D ``av`` embodiment is rejected (EC-A4).

The registry mirrors the diffusers engine's embodiment tables; the heavy engine is never imported here
(this module stays host/torch-free). ``tests/equivalence/test_action_registry_guard.py`` asserts our
tables stay byte-equal to the engine's (drift fails loudly — the S3 convention-guard lesson).

Refs: session_4/specs/embodiment-schema-validator.md; pipeline_cosmos3_omni.py
``_EMBODIMENT_TO_DOMAIN_ID`` / ``_EMBODIMENT_TO_RAW_ACTION_DIM``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionMode(Enum):
    """The action task (no string blindness)."""

    FORWARD_DYNAMICS = "forward_dynamics"
    INVERSE_DYNAMICS = "inverse_dynamics"
    POLICY = "policy"


class ErrorCode(Enum):
    """Why an action request is invalid — each maps to a 422 with an embodiment-specific message."""

    UNKNOWN_EMBODIMENT = "unknown_embodiment"
    UNSUPPORTED_FOR_INFERENCE = "unsupported_for_inference"
    WIDTH_MISMATCH = "width_mismatch"
    FRAME_WINDOW = "frame_window"
    BAD_CHUNK = "bad_chunk"
    BAD_RESOLUTION_TIER = "bad_resolution_tier"
    CONDITION_MISSING = "condition_missing"
    CONDITION_CONFLICT = "condition_conflict"


# Frozen registry (Data) — MUST equal the engine tables (convention guard). Source: pipeline_cosmos3_omni.py.
_DOMAIN_ID: dict[str, int] = {
    "no_action": 0, "av": 1, "camera_pose": 2, "hand_pose": 3, "pusht": 4, "libero": 5, "umi": 6,
    "bridge_orig_lerobot": 7, "droid_lerobot": 8, "robomind-franka": 8, "galbot": 9,
    "robomind-franka-dual": 12, "robomind-ur": 13, "agibotworld": 15, "agibot_gear_gripper": 15,
    "agibot_gear_gripper_ext": 15, "fractal": 20,
}
# Canonical (unpadded) per-embodiment action width. Domains absent here (no_action, libero) are
# unsupported for inference. All widths <= 64 (the model pads to action_dim=64).
_RAW_ACTION_DIM: dict[str, int] = {
    "av": 9, "camera_pose": 9, "pusht": 2, "umi": 10, "bridge_orig_lerobot": 10, "droid_lerobot": 10,
    "robomind-franka": 10, "robomind-franka-dual": 20, "robomind-ur": 10, "galbot": 30,
    "agibotworld": 29, "agibot_gear_gripper": 29, "agibot_gear_gripper_ext": 29, "fractal": 10,
    "hand_pose": 57,
}
# The 16-400 window governs chunk_size (the action transition count = the action sequence length the
# model rolls out) — a conservative public serving cap (INV-6). The model card states "Action: 16-400
# video frames"; the paired video is chunk_size+1, but the ±1 is immaterial for a conservative cap and
# chunk_size is the single action-length knob the caller controls. See session_4/failure_arbiter.md FA-1.
FRAME_MIN, FRAME_MAX = 16, 400
# Action conditioning resolution tiers — mirror the engine's _ACTION_RESOLUTION_BINS keys (guarded).
_RESOLUTION_TIERS: frozenset[int] = frozenset({256, 480, 704, 720})


@dataclass(frozen=True)
class ActionSpec:
    """An action request reduced to the engine-agnostic facts the validator needs (inert Data).

    ``chunk_size`` is the action transition count (the action sequence length governed by the 16-400
    window). ``raw_action_width`` is the width of a supplied ``raw_actions`` tensor (forward dynamics);
    ``None`` when no raw actions are supplied (inverse dynamics / policy infer them).
    """

    mode: ActionMode
    domain_name: str
    chunk_size: int
    raw_action_width: int | None = None
    resolution_tier: int = 480
    has_image: bool = False
    has_video: bool = False


@dataclass(frozen=True)
class ActionValidationError:
    """A structured, 422-able validation failure (no boolean/null blindness).

    ``expected``/``got`` carry the offending integers (e.g. widths) for the message; ``None`` when N/A.
    """

    code: ErrorCode
    message: str
    expected: int | None = None
    got: int | None = None


class ActionValidationFailed(ValueError):
    """Raised at the engine edge when ``validate`` rejects a request (carries the typed error → 422).

    The pure ``validate`` Calculation NEVER raises this (it returns the error as data, define-away tier);
    only the Action shell (the adapter / the future API layer) raises it to halt dispatch.
    """

    def __init__(self, error: ActionValidationError) -> None:
        self.error = error
        super().__init__(error.message)


def domain_id_of(domain_name: str) -> int | None:
    """Calculation: the engine domain id for ``domain_name`` (``None`` if unknown)."""
    return _DOMAIN_ID.get(domain_name)


def raw_action_dim_of(domain_name: str) -> int | None:
    """Calculation: the canonical unpadded action width for ``domain_name`` (``None`` if unsupported)."""
    return _RAW_ACTION_DIM.get(domain_name)


def validate(spec: ActionSpec) -> ActionValidationError | None:
    """Pure Calculation: validate an action request. ``None`` == Ok; else a typed error (maps to 422).

    Checks, in order: embodiment known -> supported-for-inference -> conditioning pairing
    (image XOR video; ID needs video; FD/policy need an image) -> resolution tier -> ``chunk_size>=1``
    -> chunk_size in [16,400] (the action-length window) -> forward-dynamics raw-action presence +
    **exact per-embodiment width**. Never raises for invalid input (define-away tier): invalid requests
    are surfaced as data the caller maps to a 422.
    """
    expected = _RAW_ACTION_DIM.get(spec.domain_name)
    if spec.domain_name not in _DOMAIN_ID:
        return ActionValidationError(
            ErrorCode.UNKNOWN_EMBODIMENT,
            f"unknown embodiment domain_name={spec.domain_name!r}; expected one of {sorted(_DOMAIN_ID)}",
        )
    if expected is None:
        return ActionValidationError(
            ErrorCode.UNSUPPORTED_FOR_INFERENCE,
            f"embodiment {spec.domain_name!r} is not supported for action inference (no canonical width); "
            f"supported: {sorted(_RAW_ACTION_DIM)}",
        )
    if spec.has_image and spec.has_video:
        return ActionValidationError(
            ErrorCode.CONDITION_CONFLICT,
            "provide either an image or a video for the action condition, not both",
        )
    if spec.mode is ActionMode.INVERSE_DYNAMICS:
        if not spec.has_video:
            return ActionValidationError(
                ErrorCode.CONDITION_MISSING, "inverse_dynamics requires video conditioning"
            )
    elif not spec.has_image:
        return ActionValidationError(
            ErrorCode.CONDITION_MISSING, f"{spec.mode.value} requires a conditioning image"
        )
    if spec.resolution_tier not in _RESOLUTION_TIERS:
        return ActionValidationError(
            ErrorCode.BAD_RESOLUTION_TIER,
            f"resolution_tier must be one of {sorted(_RESOLUTION_TIERS)}, got {spec.resolution_tier}",
            got=spec.resolution_tier,
        )
    if spec.chunk_size < 1:
        return ActionValidationError(
            ErrorCode.BAD_CHUNK, f"chunk_size must be >= 1, got {spec.chunk_size}", got=spec.chunk_size
        )
    if not (FRAME_MIN <= spec.chunk_size <= FRAME_MAX):
        return ActionValidationError(
            ErrorCode.FRAME_WINDOW,
            f"chunk_size (action length) must be in [{FRAME_MIN}, {FRAME_MAX}], got {spec.chunk_size}",
            got=spec.chunk_size,
        )
    if spec.mode is ActionMode.FORWARD_DYNAMICS:
        if spec.raw_action_width is None:
            return ActionValidationError(
                ErrorCode.CONDITION_MISSING, "forward_dynamics requires raw_actions"
            )
        if spec.raw_action_width != expected:
            return ActionValidationError(
                ErrorCode.WIDTH_MISMATCH,
                f"raw_actions width ({spec.raw_action_width}) does not match the expected width "
                f"({expected}) for domain_name={spec.domain_name!r}",
                expected=expected,
                got=spec.raw_action_width,
            )
    return None
