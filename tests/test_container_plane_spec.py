"""Spec: container-plane-lifecycle — container_generation_spec is a pure function of config."""
from __future__ import annotations

from orchestrator.planes import Plane, ProbeKind, container_generation_spec


def test_container_generation_spec_pure_health_probe():
    spec = container_generation_spec(base_url="http://vllm-omni:8000")
    assert spec.plane is Plane.GENERATION
    assert spec.probe_kind is ProbeKind.HTTP
    assert spec.probe_target == "http://vllm-omni:8000/v1/models"  # proven S1-S3 readiness endpoint


def test_container_generation_spec_custom_health_path_and_trailing_slash():
    spec = container_generation_spec(base_url="http://host:9/", health_path="/health")
    assert spec.probe_target == "http://host:9/health"
