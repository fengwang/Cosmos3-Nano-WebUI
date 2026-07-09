"""Spec: api-surface-and-errors — the typed-error → ErrorModel + status matrix (E4)."""
from __future__ import annotations

from app.auth import UnauthorizedError
from app.errors import to_error_response
from engines.vllm.context_cap import (
    ReasoningErrorCode,
    ReasoningValidationError,
    ReasoningValidationFailed,
)
from jobs.model import JobStatus, JobTransitionError
from jobs.store import IdempotencyConflict, JobNotFound
from preprocessing.action_schema import ActionValidationError, ActionValidationFailed
from preprocessing.action_schema import ErrorCode as ActionErrorCode
from preprocessing.media import MediaErrorCode, MediaValidationError, MediaValidationFailed
from preprocessing.paths import UntrustedPathError


def test_media_errors_map_to_413_415_422():
    cases = {
        MediaErrorCode.PAYLOAD_TOO_LARGE: 413,
        MediaErrorCode.UNSUPPORTED_MEDIA_TYPE: 415,
        MediaErrorCode.INVALID_DIMENSION: 422,
        MediaErrorCode.INVALID_PARAM: 422,
    }
    for code, status in cases.items():
        got_status, body = to_error_response(MediaValidationFailed(MediaValidationError(code, "m")))
        assert got_status == status
        assert body.code == code.value


def test_action_validation_maps_to_422_with_details():
    exc = ActionValidationFailed(
        ActionValidationError(ActionErrorCode.WIDTH_MISMATCH, "w", expected=9, got=10)
    )
    status, body = to_error_response(exc)
    assert status == 422 and body.code == "width_mismatch"
    assert body.details == {"expected": 9, "got": 10}


def test_reasoning_over_cap_maps_to_422():
    exc = ReasoningValidationFailed(
        ReasoningValidationError(ReasoningErrorCode.CONTEXT_OVER_CAP, "too long", expected=32768, got=40000)
    )
    status, body = to_error_response(exc)
    assert status == 422 and body.code == "context_over_cap"


def test_untrusted_path_maps_to_422():
    status, body = to_error_response(UntrustedPathError("/etc/passwd", ("/data/models",)))
    assert status == 422 and body.code == "untrusted_path"


def test_idempotency_conflict_maps_to_409():
    status, body = to_error_response(IdempotencyConflict("key1"))
    assert status == 409 and body.code == "idempotency_conflict"


def test_illegal_transition_maps_to_409():
    status, body = to_error_response(JobTransitionError(JobStatus.succeeded, JobStatus.cancelled))
    assert status == 409 and body.code == "illegal_transition"


def test_job_not_found_maps_to_404():
    status, body = to_error_response(JobNotFound("nope"))
    assert status == 404 and body.code == "not_found"


def test_unauthorized_maps_to_401():
    status, body = to_error_response(UnauthorizedError("no key"))
    assert status == 401 and body.code == "unauthorized"


def test_unknown_exception_maps_to_500():
    status, body = to_error_response(RuntimeError("boom"))
    assert status == 500 and body.code == "internal_error"
