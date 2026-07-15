# UX-S2 Sharded Review

Date: 2026-07-15
Diff reviewed: `git diff abdf65f..HEAD` (UX-S2 code + tests + deploy).
Reviewers: 5 independent read-only agents over the contract axes
(correctness, security, tests, architecture, performance).
Routing: medium risk → sharded review + adversarial verifier.

## Verdict

**No Critical/High findings.** Three concrete Medium/Low findings with strong
evidence were fixed (below); the rest were verified clean or are pre-existing /
out-of-scope nits. CPU suite **518 passed**, ruff clean after fixes.

## Findings and resolutions

| # | Axis | Sev | Finding | Resolution |
|---|---|---|---|---|
| F1 | Architecture | Low/Med | `VIDEO_MODES` (new in `engines/base.py`) was a byte-identical duplicate of the pre-existing `_ASYNC_VIDEO_MODES` in `engines/vllm_omni/work.py` — a DRY regression introduced this session; the two "video mode" facts could drift. | **Fixed** — `work.py` now aliases the canonical `_ASYNC_VIDEO_MODES = VIDEO_MODES` (imported from `engines.base`). Single source. |
| F2 | Tests | Medium | Spec scenario "`t2i` may request `resolution=720` → 720×720" had zero coverage; `default_dimensions` had no direct unit test (only exercised via `mode="t2v"`). A t2i short-circuit regression would pass all tests. | **Fixed** — added a parametrized `test_default_dimensions` in `tests/test_vllm_omni_client.py` covering video→720p, t2i→480, explicit-square-wins (video), and t2i explicit 720/256. |
| F3 | Tests | Medium | INV-P5-1 "recorded metadata == submitted form" was untested on the **default** path (the form test checked the form only; the meta test used explicit dims), so a desync in the default branch would go uncaught. | **Fixed** — added `test_meta_matches_form_on_the_720p_default_path` in `tests/test_vllm_omni_work.py`: a dims-omitted `t2v` job asserts `form["size"]=="1280x720"` AND `meta["width"/"height"]==1280/720`. |
| F4 | Tests | Low-Med | The malformed-JSON loader test asserted only `None`, not the "log once" the spec mandates for that branch. | **Fixed** — the malformed test now uses `caplog` and asserts exactly one WARNING across two calls (cache hit). |
| F5 | Tests | Low | The WebUI negative-prompt placeholder scenario is not unit-testable (vitest `include` excludes `components/studio/**`). | **Accepted + documented** — verified behaviorally via Playwright at the live run (placeholder `"Using recommended default"` renders; default draft is 1280×720). Logged as an eval seed (extend the vitest include in a future session — out of this blast radius). |
| F6 | Architecture | Low | The `resolution` schema description now narrates the mode-aware 720/480 rule that lives in `default_dimensions` (doc in two places). | **Accepted** — the schema is the OpenAPI-facing contract; documenting the default there is defensible. Noted for maintainers. |
| F7 | Security | Nit | `negative_prompt` has no `max_length` cap; an unbounded **user-supplied** value could be forwarded to the backend. | **Accepted (out of scope, pre-existing)** — the field + its lack of a cap predate UX-S2 (this session only adds an operator-trusted default); trusted-LAN posture; the field shape is out of the UX-S2 blast radius. |

## Verified clean (no findings)

- **Correctness:** precedence (user>default>omit), graceful degradation (OSError/ValueError → None, log once via lru_cache-miss), verbatim JSON transport, mode-aware default, both engine paths agree, INV-6 shape unchanged (schema regen description-only).
- **Security:** negative-prompt path derives only from `COSMOS3_MODEL_DIR` (no request input → no traversal; INV-1); no secret in log; `--no-guardrails` is **not a net-new regression** (the app already sent `extra_params.guardrails=False` at the parent commit; the compose flag aligns the server default and is flagged for UX-S4's SECURITY/README); assets mount is `:ro`, `assets/`-scoped (not weights); no committed secrets (NFR-1; `.env` gitignored; compose uses repo-relative `${VAR:-…}` defaults).
- **Performance:** the 15 KB file is read at most once/process (`lru_cache` by path); per-request cost is an env lookup + cache hit; the 15 KB string adds a sub-ms `json.dumps`+sha256 vs a seconds-to-minutes generation. Negligible. No leaks (`with open`).
- **Architecture:** `default_dimensions` correctly placed in the torch-free `engines/base.py` (no circular import); the two defaulting sites (route/edge for the file-I/O enrichment; engine layer for the pure rule) are justified by ACD; INV-P5-1 single-source preserved; the per-stack compose command divergence (fp8 offload / nvfp4 no-offload) is documented with rationale.

## Checks after fixes

- `uv run pytest -m "not gpu"` → **518 passed**.
- `uv run ruff check` (changed files) → clean.
