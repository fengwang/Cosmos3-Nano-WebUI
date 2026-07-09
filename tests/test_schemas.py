"""Spec: shared-schemas — async job-model types + error model (Data layer)."""
import pytest
from pydantic import ValidationError

from app.schemas import ErrorModel, HealthStatus, Job, JobStatus


def test_jobstatus_has_the_five_states():
    # specs/shared-schemas.md :: Job and JobStatus appear as components
    assert {s.value for s in JobStatus} == {
        "queued",
        "running",
        "succeeded",
        "failed",
        "cancelled",
    }


def test_errormodel_requires_code_and_message():
    # specs/shared-schemas.md :: ErrorModel appears as a component
    e = ErrorModel(code="invalid_input", message="bad")
    assert e.code == "invalid_input" and e.message == "bad"
    with pytest.raises(ValidationError):
        ErrorModel(code="missing_message")  # message is required


def test_job_uses_enum_and_bounded_progress():
    j = Job(id="j-1", status=JobStatus.queued, mode="t2v", created_at="2026-06-21T00:00:00Z")
    assert j.status is JobStatus.queued
    assert j.progress == 0.0
    with pytest.raises(ValidationError):
        Job(id="j-2", status=JobStatus.running, mode="t2v", created_at="t", progress=1.5)


def test_healthstatus_minimal():
    assert HealthStatus(status="ready").status == "ready"
