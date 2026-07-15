"""Curated negative-prompt default (ACD: a pure path Calculation + one cached Action).

The API applies the model's curated negative prompt as an OVERRIDABLE default when a
generation request omits ``negative_prompt`` (FR-4, INV-5). The file path is derived from
the configurable ``COSMOS3_MODEL_DIR`` mount — never a hardcoded absolute path (INV-1) —
and a missing / unreadable / malformed file degrades gracefully (log once, no default)
rather than crashing generation (R-03). Transport is the file's verbatim JSON text carried
by the existing ``negative_prompt: str`` field (R-04 decision: the pipeline consumes a
serialized-JSON prompt string; the API + vLLM-Omni form + diffusers arg are all strings —
so no schema-shape change, INV-6). Refs: session_2/specs/negative-prompt-default.md.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache

_LOG = logging.getLogger("cosmos3.preprocessing.negative_prompt")

# Relative to the model directory; the curated asset ships under each checkpoint's assets/ (E-06).
_ASSET_RELPATH = ("assets", "negative_prompt.json")


def negative_prompt_path(model_dir: str) -> str:
    """Pure: the curated negative-prompt file path under a model directory."""
    return os.path.join(model_dir, *_ASSET_RELPATH)


@lru_cache(maxsize=8)
def _read_default(path: str) -> str | None:
    """Action (cached by path): read + validate the curated file; ``None`` on any failure.

    The file is read at most once per path per process (the ~15 KB asset is not re-read on
    every request). ``json.loads`` is a well-formedness gate only — the transported value is
    the file's verbatim text. A cache hit skips this body, so a failure logs exactly once.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        json.loads(text)  # validity gate only; the transported bytes stay verbatim
    except (OSError, ValueError) as exc:
        _LOG.warning("negative-prompt default unavailable at %s (%s); proceeding without it", path, exc)
        return None
    return text


def load_default_negative_prompt() -> str | None:
    """Action: the curated default from ``${COSMOS3_MODEL_DIR}/assets/negative_prompt.json``.

    Returns the verbatim JSON text, or ``None`` when the model directory is unset or the file
    is missing / unreadable / malformed (graceful degradation — the caller then omits the field
    and generation proceeds with no negative prompt).
    """
    model_dir = os.environ.get("COSMOS3_MODEL_DIR")
    if not model_dir:
        return None
    return _read_default(negative_prompt_path(model_dir))
