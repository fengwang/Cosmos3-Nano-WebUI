# P2 — Reasoning HTTP 400 fix (reasoner context-cap drift), FP8, GPU

Date: 2026-07-25 · Session AM-S4 (owner-authorized amendment) · RTX 5090 (sm_120).

## Symptom
WebUI Reasoning tab, prompt "How chopsticks are made?" → browser shows **HTTP Error 400**. The
`cosmos3-nano-webui-vllm-reasoner` logs: `POST /v1/chat/completions 400 Bad Request`.

## Root cause — config drift (api window 32768 vs reasoner 8192)
The reasoner is served with **`--max-model-len 8192`** (AM-S2; reasoner log: `max_seq_len=8192`). The
api's `ContextCapConfig` defaults to `max_context_tokens = max_output_tokens = 32768`
(`api/engines/vllm/context_cap.py`; its comment even claims "== the vLLM max_model_len"), and **no
`COSMOS3_REASONER_MAX_*` env was set** to align it. The WebUI sends `/v1/reason` with **no
`max_output_tokens`** (`webui/components/chat/ChatStream.tsx:96` — "the backend context window is the only
ceiling"), so the api computes `effective = min(32768, 32768 − prompt) ≈ 32760`, **passes its own
(wrong-window) edge validation**, and forwards `max_tokens ≈ 32760` to the 8192-window reasoner → the
reasoner rejects it with HTTP 400, which the api relays as `str(HTTPError)="HTTP Error 400: Bad Request"`
in an SSE `error` event the WebUI displays. The AM-S4 all-modes smoke missed this because it passed an
explicit `max_output_tokens=64`. Secondary: the api's `count_tokens` char-heuristic counts the *raw*
prompt, not the chat-template-wrapped form, so aligning to *exactly* 8192 would still overflow at the
boundary → the fix reserves headroom.

## Reproduction (before)
- `POST /v1/reason {"prompt":"How chopsticks are made?"}` → `event: error {"message":"HTTP Error 400: Bad
  Request"}` (matches the owner's report).
- Control `POST /v1/reason {"prompt":"…","max_output_tokens":64}` → streams tokens (works).
- api env probe: no `COSMOS3_REASONER_MAX_*` set → the 32768 default was in force.

## Fix (deploy/env; no code change)
`deploy/docker-compose.fp8.yml` api.environment:
```
COSMOS3_REASONER_MAX_CONTEXT: "7680"   # 8192 − 512 chat-template headroom
COSMOS3_REASONER_MAX_OUTPUT:  "7680"
```
The api now models the reasoner's real window. An unbounded request yields `effective = 7680 − prompt`
(fits the 8192 window with ≥512-token headroom for the template the api can't count), and any genuine
over-cap request gets a clean **422 at the api edge** (`context_over_cap`), never a reasoner 400. The
`COSMOS3_REASONER_MAX_CONTEXT` env knob already existed for exactly this (`ContextCapConfig.from_env`).

## Verification (after)
- `POST /v1/reason {"prompt":"How chopsticks are made?"}` (no cap — the WebUI's exact shape) → streams
  coherent text: *"Chopsticks are made through a process that varies depending on the material—wood,
  bamboo…"*. **Fixed.**
- Regression guard: `tests/deploy/test_reasoner_context_cap_fits_model_len.py` asserts the api cap ≤ the
  reasoner `--max-model-len` − 128 headroom **and** output ≤ context (catches any future re-drift). Red
  before the fix (env absent → KeyError), green after. `tests/deploy` = 12 passed.
- Full CPU suite exit 0; fp8 `config` still **0 BF16 mounts** + the caps rendered; `openapi.json` unchanged.

## Follow-ups
- **AM-S5:** when it adds an nvfp4 reasoner, set the analogous nvfp4 cap + extend the guard test.
- **Hardening (future):** the api could DISCOVER the reasoner's `max_model_len` at runtime (query
  `/v1/models` / the served model config) instead of a hardcoded env, eliminating this drift class
  entirely (single source of truth = the reasoner).
