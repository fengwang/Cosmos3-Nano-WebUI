"""Pinned identifiers shared by every GPU-S3 probe (Data only — no functions).

Values are copied from docs/eval_seed_cases.md's "Public Checkpoint IDs" section and
docs/model_setup.md §1 (both already updated by GPU-S2); this module does not
re-derive or look them up, so a re-pin sweep still only needs to touch the docs.
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

# Generated artifacts (images/video) are evidence attachments for human spot-checking only —
# project_contract.md §6 forbids committing "generated media" to this repository, and .gitignore
# is outside this session's blast radius to extend, so artifacts never live under docs/session_3/.
# The evidence_*.json fragments (which ARE committed) carry metadata (dims, format, size, sha256),
# not the binary, and cite the artifact by filename only — never this directory's absolute path,
# which is host-specific and must not be committed (project_contract.md INV-1).
ARTIFACT_DIR = Path(tempfile.gettempdir()) / "gpu-s3-artifacts"

# A subprocess failure's exception message embeds its full argv, which can include either
# of these two absolute prefixes (the repo checkout path, the host's temp dir) — every
# run_*.py script's exception boundary passes its `notes` text through
# lib.sanitize_error_text with this tuple before writing evidence, so a *future* subprocess
# failure can't reopen the same INV-1 leak this session already found and fixed once
# (constants.py's own ARTIFACT_DIR/checkpoint paths, before that fix).
REDACT_PREFIXES = (str(Path(__file__).resolve().parents[3]), tempfile.gettempdir())


@dataclass(frozen=True)
class CheckpointSpec:
    repo_id: str
    revision: str
    local_dir: str


CHECKPOINTS: dict[str, CheckpointSpec] = {
    "fp8": CheckpointSpec(
        repo_id="wfen/Cosmos3-Nano-FP8-Blockwise",
        revision="9bf5d6ae164688487bdb71947ccc6ebe70d12900",
        local_dir="models/Cosmos3-Nano-FP8-Blockwise",
    ),
    "nvfp4": CheckpointSpec(
        repo_id="wfen/Cosmos3-Nano-NVFP4-Blockwise",
        revision="5514c42b9759739f545e0d0dee453db8d8525fbc",
        local_dir="models/Cosmos3-Nano-NVFP4-Blockwise",
    ),
}

VLLM_OMNI_COMMIT = "697035018b70cef76b974a909d23371a9984c3f2"

# deploy/vllm-omni.Dockerfile's own comment: guardrails stay ON by default; --no-guardrails
# is meant to be an explicit runtime Compose `command:` override, never baked into the
# shipped default. R-10 (closing the guardrails-on path) is explicitly out of scope for
# GPU-S3 (owner decision, brainstorming.md) — this session runs the same way GPU-S1 did,
# via an override file generated at runtime into a temp path (never committed, matching
# GPU-S1's own "undocumented in any tracked file" approach) rather than editing any tracked
# compose file (deploy/docker-compose.*.yml is outside this session's blast radius either way).
NO_GUARDRAILS_OVERRIDE_YAML = """\
services:
  vllm-omni:
    command:
      - vllm
      - serve
      - /models/checkpoint
      - --omni
      - --host
      - 0.0.0.0
      - --port
      - "8000"
      - --init-timeout
      - "1800"
      - --no-guardrails
"""

# Fixed across every T2I probe (direct + full-stack, both checkpoints) this session, so results
# are comparable; recorded in each evidence fragment's request_shape rather than hidden.
T2I_PROMPT = "a red apple on a wooden table, studio lighting"
T2I_SEED = 42
T2I_DIMENSION = 480  # one of the documented supported sizes (docs/model_setup.md §9)

# .env's own COSMOS3_API_KEY line is "COSMOS3_API_KEY=                # empty = auth
# disabled...": the value is genuinely empty, but neither a naive split-on-"=" parser (this
# session's own first attempt) nor Docker Compose's own .env parsing strips the inline
# comment — both read the trailing comment text as if it were the key, and happened to
# match by coincidence rather than exercising a real configured secret. Rather than lean on
# that ambiguous parse (or edit .env, which is outside this session's blast radius), the
# full-stack probe defines and injects its own test key via an explicit env override
# (compose_lifecycle.bring_up's extra_env), the same mechanism already used for the
# checkpoint-mount override, so the X-API-Key path is genuinely exercised end to end.
FULLSTACK_TEST_API_KEY = "gpu-s3-fullstack-test-key-2026-07-09"
