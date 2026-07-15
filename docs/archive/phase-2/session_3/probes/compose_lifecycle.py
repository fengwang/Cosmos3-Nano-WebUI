"""Action shell: compose stack lifecycle shared by every generation probe. Only one of the
fp8/nvfp4 overlays can be up at a time (they share a fixed container name), so every caller
brings up, uses, and tears down its stack before the next probe starts.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from constants import CHECKPOINTS, NO_GUARDRAILS_OVERRIDE_YAML
from lib import Verdict, check_dockerfile_unmodified

REPO_ROOT = Path(__file__).resolve().parents[3]

# deploy/docker-compose.{fp8,nvfp4}.yml bind-mount the checkpoint via
# ${COSMOS3_FP8_DIR:-../models/...}/${COSMOS3_NVFP4_DIR:-../models/...} — the repo's own
# .env pins these to /data/models/Cosmos3-Nano-*-Blockwise (a stale, pre-fix, manually
# LFS-patched local copy from an earlier session; confirmed live via `git log` inside it and
# a raw LFS-pointer read of BIAS.md), which silently outranks the compose file's own
# repo-relative default. Sharded review (correctness axis) caught this: every generation
# probe that only did `docker compose --env-file .env ... up -d` was mounting that stale
# directory, never T1's fresh download. Fixed by overriding the env var explicitly (process
# env verified live to outrank --env-file's value) plus a preflight that fails loudly on
# any resolution mismatch, rather than trusting the override silently took effect.
_ENV_VAR_BY_CHECKPOINT = {"fp8": "COSMOS3_FP8_DIR", "nvfp4": "COSMOS3_NVFP4_DIR"}


def compose_file(checkpoint: str) -> str:
    return f"deploy/docker-compose.{checkpoint}.yml"


def _write_no_guardrails_override() -> str:
    """Write the static override content to a fresh temp file; returns its path.

    Written at runtime (never a fixed, committed path) so no host-specific path needs to
    be hardcoded anywhere — only the static YAML content (Data) lives in constants.py.
    """
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", prefix="gpu-s3-no-guardrails-", delete=False,
    )
    with handle:
        handle.write(NO_GUARDRAILS_OVERRIDE_YAML)
    return handle.name


def _checkpoint_env(checkpoint: str) -> tuple[dict[str, str], Path]:
    """Explicit env override pointing the compose mount at T1's fresh download, regardless
    of what .env pins. Returns (env, expected_absolute_mount_source).
    """
    fresh_dir = REPO_ROOT / CHECKPOINTS[checkpoint].local_dir
    env = {**os.environ, _ENV_VAR_BY_CHECKPOINT[checkpoint]: str(fresh_dir)}
    return env, fresh_dir


def _dockerfile_is_unmodified() -> bool:
    """Distinguishes "git diff found a real diff" (exit 1) from "git itself failed" (any
    other nonzero exit, e.g. 128) — a bare `bool(returncode)` would misreport the latter as
    the former. Either way `bring_up` refuses to proceed; the two cases just get a different
    error message so a real git problem isn't misdiagnosed as a dirty Dockerfile.
    """
    result = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", "deploy/vllm-omni.Dockerfile"],
        cwd=REPO_ROOT, capture_output=True, timeout=30,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"git diff check itself failed (exit {result.returncode}): {result.stderr!r}")
    return check_dockerfile_unmodified(has_uncommitted_diff=bool(result.returncode)) == Verdict.PASS


def _verify_mount_source(checkpoint: str, env: dict[str, str], expected: Path) -> None:
    """Preflight: resolve `docker compose config` with the SAME flags/env `bring_up` will
    actually use, and fail loudly if the effective bind-mount source is not exactly
    `expected` — never assume the override silently took effect.
    """
    result = subprocess.run(
        [
            "docker", "compose", "--env-file", ".env",
            "-f", compose_file(checkpoint), "config", "--format", "json",
        ],
        cwd=REPO_ROOT, env=env, check=True, timeout=60, capture_output=True, text=True,
    )
    volumes = json.loads(result.stdout)["services"]["vllm-omni"]["volumes"]
    sources = [v["source"] for v in volumes if v.get("target") == "/models/checkpoint"]
    if sources != [str(expected)]:
        raise RuntimeError(
            f"checkpoint mount resolved to {sources!r}, expected [{expected!s}] — "
            "refusing to bring up against an unverified mount"
        )


def bring_up(checkpoint: str, *, extra_env: dict[str, str] | None = None) -> None:
    """Bring up `checkpoint`'s stack against T1's fresh checkpoint download (never a
    `.env`-pinned or otherwise pre-existing local directory — verified, not assumed) and
    with guardrails off (R-10 explicitly out of scope for GPU-S3) via a runtime-generated
    Compose `command:` override, never an edit to any tracked compose file.

    `--env-file .env` is kept (not dropped) so every other operator setting `.env` carries
    still applies; `extra_env` layers on top for callers that need one more explicit
    override (e.g. a session-defined API key — see run_fullstack_t2i.py) beyond the
    checkpoint-mount override this function always applies.

    Also the single chokepoint for the Dockerfile-freshness guard: every caller (direct,
    full-stack, T2V) goes through here, so none of them can independently forget it.
    """
    if not _dockerfile_is_unmodified():
        raise RuntimeError(
            "deploy/vllm-omni.Dockerfile has an uncommitted diff; refusing to trust the "
            "cached cosmos3-nano-vllm-omni:local image"
        )
    env, fresh_dir = _checkpoint_env(checkpoint)
    if extra_env:
        env.update(extra_env)
    _verify_mount_source(checkpoint, env, fresh_dir)
    override_path = _write_no_guardrails_override()
    try:
        subprocess.run(
            [
                "docker", "compose", "--env-file", ".env",
                "-f", compose_file(checkpoint), "-f", override_path, "up", "-d",
            ],
            cwd=REPO_ROOT, env=env, check=True, timeout=300,
        )
    finally:
        os.unlink(override_path)


def tear_down() -> None:
    """Idempotent — safe to call even if nothing (or only part of a stack) is up."""
    subprocess.run(["make", "down"], cwd=REPO_ROOT, check=False, timeout=120)
