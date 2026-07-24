# UX-S2 Tasks

Ordered by dependency. Each task is verifiable and small enough for one loop.
Specs: `docs/session_2/specs/*.md`. Design: `docs/session_2/design.md`.

## 1. Negative-prompt default (server)

- [ ] 1.1 Add `api/preprocessing/negative_prompt.py`: pure
  `negative_prompt_path(model_dir)` + cached Action `load_default_negative_prompt()`
  returning verbatim text or `None` (unset var / missing / unreadable / malformed),
  logging once. (spec: negative-prompt-default)
- [ ] 1.2 Wire into `api/app/routes/generation.py` `_params(...)` with precedence
  user → default → omit. (spec: negative-prompt-default)
- [ ] 1.3 Tests: `tests/api/test_negative_prompt_default.py` (path, present, missing,
  unset, malformed, cached, no-abs-path); extend `tests/api/test_routes_generation.py`
  (default applied / user overrides / none). (`EV-UX-NEGPROMPT-*`)

## 2. Video resolution mode-aware default (server)

- [ ] 2.1 `api/engines/vllm_omni/client.py` `resolved_params()`: mode-aware dims
  (video → 1280×720, `t2i` → 480; explicit width/height/resolution win). (spec:
  video-resolution-default)
- [ ] 2.2 `api/orchestrator/gen_worker.py` `_to_generation_request()`: same
  mode-aware default (reads `request["mode"]`). (spec: video-resolution-default)
- [ ] 2.3 `api/app/schemas.py:96`: update the `resolution` field description only.
- [ ] 2.4 Tests: extend `tests/test_vllm_omni_client.py` + a gen_worker mapping test
  (t2v/i2v/t2v_audio → 1280×720; t2i → 480; explicit wins; metadata==form).
  (`EV-UX-RESOLUTION-DEFAULT-VIDEO-720`)

## 3. WebUI defaults + affordance

- [ ] 3.1 `webui/lib/studio/draft.ts`: `DEFAULT_PRESET → "hi-720"`.
- [ ] 3.2 `webui/components/studio/ComposePanel.tsx`: negative-prompt
  `placeholder="Using recommended default"`.
- [ ] 3.3 Tests: `initialDraft()` → hi-720/1280×720/49; blank-negative omit;
  placeholder present.

## 4. Deterministic verification

- [ ] 4.1 Regenerate OpenAPI if the description change alters it; `tests/test_openapi.py`.
- [ ] 4.2 CPU suite: `uv run pytest -m "not gpu"`.
- [ ] 4.3 WebUI: `cd webui && pnpm build && pnpm lint && pnpm typecheck && pnpm test`.
- [ ] 4.4 Scoped path check: `rg -n "/data/models" api/preprocessing/negative_prompt.py`
  (clean) + confirm the 6 pre-existing `api/` fallbacks are unchanged.

## 5. Live 5090 720p GPU smoke (owner elected)

- [ ] 5.1 Bring up the FP8 stack; `POST /v1/generation/t2v` 1280×720 @ 49 frames,
  `negative_prompt` omitted; record peak VRAM, artifact, server-log `negative` line.
- [ ] 5.2 Repeat for NVFP4.
- [ ] 5.3 Record evidence (`EV-UX-GPU-720-FP8-T2V`, `-NVFP4-T2V`,
  `-NEGPROMPT-APPLIED`) into `docs/evidence_map.md` with the full evidence fields;
  on environment friction, classify ENVIRONMENT and record an owner-visible deferral.

## 6. Review + close

- [ ] 6.1 Sharded review (correctness, security, tests, architecture, performance);
  fix High/Critical; re-check. → `docs/session_2/sharded_review.md`.
- [ ] 6.2 Adversarial verification (fresh context). → `docs/session_2/adversarial_verification.md`.
- [ ] 6.3 Verify `GATE-UX-S2-DEFAULTS`; update `evidence_map.md`, `risk_register.md`,
  `eval_seed_cases.md`; write `docs/handoff.md`; add eval seeds to `docs/eval_corpus/`.
