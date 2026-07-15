# UX-S2 Sharded Review

Date: 2026-07-15
Diff reviewed: `git diff abdf65f..HEAD` (UX-S2 code + tests + deploy).
Reviewers: **6** independent read-only agents over the full axis set in
`docs/agent_workflow/prompts/sharded_review.md` — correctness, **readability/
simplicity**, security, tests, architecture, performance.
Routing: medium risk → sharded review + adversarial verifier.

**Process correction (owner-caught):** the first pass ran only the 5 axes listed
in `session_2_contract.yaml`'s `review_axes:` and folded readability away. The
updated sharded-review *prompt* requires 6 (it adds readability/simplicity); the
owner flagged the omission and the 6th reviewer was then run (findings F8–F10).
Lesson harvested in `docs/eval_corpus/ux-s2-generation-defaults.md` §5: the prompt
is the authoritative how-to; a contract's `review_axes` is a minimum, not a cap.

## Verdict

**No Critical/High findings** across all 6 axes. Fixed: **F2/F3/F4** (test-coverage
gaps) + **F9** (readability docstring). **F1** (arch dedup) **deferred** — its fix
would edit `work.py`, out of the blast radius. **F8** moot (depended on F1). F5/F6/F7/
F10 accepted (out-of-scope / pre-existing / style). Readability reviewer judged the
diff "unusually well-documented," ACD-consistent, no dead code. CPU suite **518 passed**,
ruff clean.

## Findings and resolutions

| # | Axis | Sev | Finding | Resolution |
|---|---|---|---|---|
| F1 | Architecture | Low/Med | `VIDEO_MODES` (new in `engines/base.py`) is a byte-identical duplicate of the pre-existing `_ASYNC_VIDEO_MODES` in `engines/vllm_omni/work.py`; the two "video mode" facts could drift. | **Deferred (out of blast radius)** — the dedup fix requires editing `api/engines/vllm_omni/work.py`, which is **not** in the UX-S2 `allowed_files`. An initial fix + its follow-on Nit (F8) were reverted to respect the boundary (AGENTS.md; caught by the adversarial verifier). The minor cross-module duplication (base's `VIDEO_MODES` for the 720p default vs work's `_ASYNC_VIDEO_MODES` for async dispatch — both correct today) is left as a follow-up. |
| F2 | Tests | Medium | Spec scenario "`t2i` may request `resolution=720` → 720×720" had zero coverage; `default_dimensions` had no direct unit test (only exercised via `mode="t2v"`). A t2i short-circuit regression would pass all tests. | **Fixed** — added a parametrized `test_default_dimensions` in `tests/test_vllm_omni_client.py` covering video→720p, t2i→480, explicit-square-wins (video), and t2i explicit 720/256. |
| F3 | Tests | Medium | INV-P5-1 "recorded metadata == submitted form" was untested on the **default** path (the form test checked the form only; the meta test used explicit dims), so a desync in the default branch would go uncaught. | **Fixed** — added `test_meta_matches_form_on_the_720p_default_path` in `tests/test_vllm_omni_work.py`: a dims-omitted `t2v` job asserts `form["size"]=="1280x720"` AND `meta["width"/"height"]==1280/720`. |
| F4 | Tests | Low-Med | The malformed-JSON loader test asserted only `None`, not the "log once" the spec mandates for that branch. | **Fixed** — the malformed test now uses `caplog` and asserts exactly one WARNING across two calls (cache hit). |
| F5 | Tests | Low | The WebUI negative-prompt placeholder scenario is not unit-testable (vitest `include` excludes `components/studio/**`). | **Accepted + documented** — verified behaviorally via Playwright at the live run (placeholder `"Using recommended default"` renders; default draft is 1280×720). Logged as an eval seed (extend the vitest include in a future session — out of this blast radius). |
| F6 | Architecture | Low | The `resolution` schema description now narrates the mode-aware 720/480 rule that lives in `default_dimensions` (doc in two places). | **Accepted** — the schema is the OpenAPI-facing contract; documenting the default there is defensible. Noted for maintainers. |
| F7 | Security | Nit | `negative_prompt` has no `max_length` cap; an unbounded **user-supplied** value could be forwarded to the backend. | **Accepted (out of scope, pre-existing)** — the field + its lack of a cap predate UX-S2 (this session only adds an operator-trusted default); trusted-LAN posture; the field shape is out of the UX-S2 blast radius. |
| F8 | Readability | Nit | The F1 dedup made `_ASYNC_VIDEO_MODES` a single-use alias. | **Moot** — F1 was reverted (out of radius), so `work.py` is unchanged and this alias never exists. |
| F9 | Readability | Nit | `default_dimensions` docstring was a dense 4-line run-on. | **Fixed** — split into a one-line summary + short body. |
| F10 | Readability | Nit | The three single-line `JobSubmit(...)` route handlers grew to ~145 chars (`t2v_audio` already uses the multi-line form). Not a lint break (E501 not enforced); pre-existing house style. | **Accepted** — no rule break, no behavior change; consistency tidy deferred as optional. |

## Verified clean (no findings)

- **Correctness:** precedence (user>default>omit), graceful degradation (OSError/ValueError → None, log once via lru_cache-miss), verbatim JSON transport, mode-aware default, both engine paths agree, INV-6 shape unchanged (schema regen description-only).
- **Security:** negative-prompt path derives only from `COSMOS3_MODEL_DIR` (no request input → no traversal; INV-1); no secret in log; `--no-guardrails` is **not a net-new regression** (the app already sent `extra_params.guardrails=False` at the parent commit; the compose flag aligns the server default and is flagged for UX-S4's SECURITY/README); assets mount is `:ro`, `assets/`-scoped (not weights); no committed secrets (NFR-1; `.env` gitignored; compose uses repo-relative `${VAR:-…}` defaults).
- **Performance:** the 15 KB file is read at most once/process (`lru_cache` by path); per-request cost is an env lookup + cache hit; the 15 KB string adds a sub-ms `json.dumps`+sha256 vs a seconds-to-minutes generation. Negligible. No leaks (`with open`).
- **Architecture:** `default_dimensions` correctly placed in the torch-free `engines/base.py` (no circular import); the two defaulting sites (route/edge for the file-I/O enrichment; engine layer for the pure rule) are justified by ACD; INV-P5-1 single-source preserved; the per-stack compose command divergence (fp8 offload / nvfp4 no-offload) is documented with rationale.

## Checks after fixes

- `uv run pytest -m "not gpu"` → **518 passed**.
- `uv run ruff check` (changed files) → clean.
