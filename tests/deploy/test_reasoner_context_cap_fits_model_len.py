"""The api's reasoning context cap must fit the reasoner's `--max-model-len` (with headroom) — BOTH stacks.

Guards the config drift that 400'd the WebUI Reasoning tab: the api defaulted its reasoning context
window to 32768 while the `vllm-reasoner` serves `--max-model-len 8192`, so an unbounded `/v1/reason`
forwarded `max_tokens ≈ 32760` and the reasoner rejected it with HTTP 400. The api's char-heuristic
prompt count also can't see the chat-template tokens, so the api cap must sit BELOW the reasoner's
window by a headroom margin (an over-cap request then gets a clean 422 at the api edge, not a 400).

AM-S5: parametrized over the fp8 AND nvfp4 stacks — the nvfp4 reasoner (W4A16) uses the same
`--max-model-len 8192` and the same api caps, so both stacks are guarded against the drift.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
MIN_TEMPLATE_HEADROOM = 128  # tokens reserved for the chat-template overhead the api cannot count


def _stack(name: str) -> dict:
    return yaml.safe_load((ROOT / f"deploy/docker-compose.{name}.yml").read_text())


def _reasoner_max_model_len(stack: dict) -> int:
    cmd = stack["services"]["vllm-reasoner"]["command"]
    for i, tok in enumerate(cmd):
        if str(tok) == "--max-model-len":
            return int(cmd[i + 1])
    raise AssertionError("vllm-reasoner command has no --max-model-len")


def _api_reasoner_caps(stack: dict) -> tuple[int, int]:
    env = stack["services"]["api"]["environment"]
    return int(env["COSMOS3_REASONER_MAX_CONTEXT"]), int(env["COSMOS3_REASONER_MAX_OUTPUT"])


@pytest.mark.parametrize("name", ["fp8", "nvfp4"])
def test_api_reasoning_cap_fits_reasoner_window_with_headroom(name: str):
    stack = _stack(name)
    max_model_len = _reasoner_max_model_len(stack)
    max_ctx, max_out = _api_reasoner_caps(stack)
    assert max_ctx <= max_model_len - MIN_TEMPLATE_HEADROOM, (
        f"[{name}] api COSMOS3_REASONER_MAX_CONTEXT={max_ctx} must be ≤ reasoner --max-model-len "
        f"{max_model_len} − {MIN_TEMPLATE_HEADROOM} headroom, else an unbounded /v1/reason forwards a "
        f"max_tokens the reasoner 400s"
    )
    assert max_out <= max_ctx, f"[{name}] output ceiling {max_out} must not exceed the context window {max_ctx}"
