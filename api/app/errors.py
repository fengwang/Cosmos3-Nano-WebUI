"""Typed-error → ErrorModel + HTTP-status mapping (ACD: one pure table + FastAPI handlers; E4).

Every domain error is errors-as-data; this is the single place that assigns it an HTTP status and an
`ErrorModel`, so no route hand-rolls a status code (the EC-S3/EC-A4/EC-S6 matrix lives here). The pure
`to_error_response` is host-testable; `install_error_handlers` wires it into the app. Refs:
session_6/specs/api-surface-and-errors.md.
"""
from __future__ import annotations

from app.routes.checkpoint import CheckpointUnavailable
from app.schemas import ErrorModel
from engines.vllm.context_cap import ReasoningValidationFailed
from jobs.model import JobTransitionError
from jobs.store import IdempotencyConflict, JobNotFound
from preprocessing.action_schema import ActionValidationFailed
from preprocessing.media import MediaErrorCode, MediaValidationFailed
from preprocessing.paths import UntrustedPathError

_MEDIA_STATUS = {
    MediaErrorCode.PAYLOAD_TOO_LARGE: 413,
    MediaErrorCode.UNSUPPORTED_MEDIA_TYPE: 415,
    MediaErrorCode.INVALID_DIMENSION: 422,
    MediaErrorCode.INVALID_PARAM: 422,
}


def _details(err: object) -> dict | None:
    out: dict = {}
    for field in ("expected", "got"):
        value = getattr(err, field, None)
        if value is not None:
            out[field] = value
    return out or None


def to_error_response(exc: Exception) -> tuple[int, ErrorModel]:
    """Pure: map a typed domain error to ``(status, ErrorModel)``. Unknown → 500 (generic)."""
    if isinstance(exc, MediaValidationFailed):
        err = exc.error
        return _MEDIA_STATUS[err.code], ErrorModel(code=err.code.value, message=err.message, details=_details(err))
    if isinstance(exc, (ActionValidationFailed, ReasoningValidationFailed)):
        err = exc.error
        return 422, ErrorModel(code=err.code.value, message=err.message, details=_details(err))
    if isinstance(exc, UntrustedPathError):
        return 422, ErrorModel(code="untrusted_path", message=str(exc))
    if isinstance(exc, CheckpointUnavailable):
        return 422, ErrorModel(code=CheckpointUnavailable.code, message=str(exc))
    if isinstance(exc, IdempotencyConflict):
        return 409, ErrorModel(code="idempotency_conflict", message=str(exc))
    if isinstance(exc, JobTransitionError):
        return 409, ErrorModel(code="illegal_transition", message=str(exc))
    if isinstance(exc, JobNotFound):
        return 404, ErrorModel(code="not_found", message=str(exc))
    return 500, ErrorModel(code="internal_error", message="internal server error")


def install_error_handlers(app) -> None:
    """Action (app assembly): register `to_error_response` as the handler for every typed domain error."""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    def handle(_request: "Request", exc: Exception) -> "JSONResponse":
        status, body = to_error_response(exc)
        return JSONResponse(status_code=status, content=body.model_dump())

    for exc_type in (
        MediaValidationFailed,
        ActionValidationFailed,
        ReasoningValidationFailed,
        UntrustedPathError,
        CheckpointUnavailable,
        IdempotencyConflict,
        JobTransitionError,
        JobNotFound,
    ):
        app.add_exception_handler(exc_type, handle)
