"""Spec: trust-boundary — no request-supplied path can reach torch.load (INV-8 / EC-S6, static).

The pickle loaders (`torch.load(weights_only=False)`) are an RCE surface (RK-10). This asserts
structurally that ``torch.load`` exists ONLY in the frozen engine loaders (which take env/config model
dirs), never in the S6 request-handling code (app/jobs/orchestrator/preprocessing), and that the public
job-submission schema has no checkpoint/model-dir field a request could use to redirect a loader.
"""
from __future__ import annotations

import ast
import pathlib

API_ROOT = pathlib.Path(__file__).resolve().parents[2] / "api"


def _calls_torch_load(source: str) -> bool:
    """True iff the source has an actual ``torch.load(...)`` CALL (AST — ignores docstrings/comments)."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "load"
                and isinstance(func.value, ast.Name)
                and func.value.id == "torch"
            ):
                return True
    return False


def test_torch_load_only_in_frozen_engine_loaders():
    offenders: list[str] = []
    for py in API_ROOT.rglob("*.py"):
        if _calls_torch_load(py.read_text(encoding="utf-8")):
            rel = py.relative_to(API_ROOT).as_posix()
            if not rel.startswith("engines/"):  # permitted only in the frozen, env-driven engine loaders
                offenders.append(rel)
    assert offenders == [], f"torch.load() reachable from non-engine (request-handling) code: {offenders}"


def test_job_submission_schema_has_no_checkpoint_field():
    from app.schemas import JobSubmit

    forbidden = {"model_dir", "checkpoint", "checkpoint_dir", "ckpt", "weights", "weights_path"}
    assert not (forbidden & set(JobSubmit.model_fields)), (
        "JobSubmit must not expose a checkpoint/model-dir field (INV-8: model dirs come from env/config only)"
    )


def test_orchestrator_gen_worker_loads_from_env_config_only():
    # the generation worker resolves its model dir via *.from_env() (env), never a request arg.
    # S7 (design D-2): the worker now loads the action-enabled pipeline serving both generation+action,
    # so the env-config source is ActionEngineConfig.from_env (COSMOS3_MODEL_DIR / COSMOS3_BASE_ACTION_DIR).
    src = (API_ROOT / "orchestrator" / "gen_worker.py").read_text(encoding="utf-8")
    assert "ActionEngineConfig.from_env()" in src  # env-config model dir only (INV-8)
    assert "sys.argv[1]" in src  # the only CLI arg is the ready-file path (not a model path)
