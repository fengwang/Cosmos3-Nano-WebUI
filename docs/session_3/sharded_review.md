# AM-S3 Sharded Review

Date: 2026-07-25 · Session: AM-S3 · Risk: high. Three independent, read-only, fresh-context reviewers
over the six axes (correctness+tests; security+architecture; readability+performance), per
`docs/agent_workflow/prompts/sharded_review.md`. Diff: 6 files, +335 (action serving via the omni
video-API `action_mode`; retire the BF16 base default). Deduplicated findings + dispositions below.

## Findings

| # | Severity | Axis | Location | Finding | Disposition |
|---|---|---|---|---|---|
| 1 | **Medium** | correctness / robustness (2 reviewers) | `client.py` `run_action_job` completion guard | The guard rejected only a `None` `data`, so a degenerate server reply (`action.data == []` or a non-list) yielded a silently-empty trajectory artifact (ID) / empty sidecar (policy), or an **untyped `TypeError`** on the later `list()` coercion. The server reply is untrusted external data; "no silent wrong result" was enforced for an empty *rollout* (policy) but not for an empty *trajectory*. | **FIXED** — guard now requires a non-empty `list`: `not isinstance(action, dict) or not isinstance(action.get("data"), list) or not action["data"]` → typed `generation_failed`, no artifact. |
| 2 | Low | tests | `tests/test_vllm_omni_work.py` | No test for degenerate `action.data` or for a `failed`/typed-fail poll on the async action path. | **FIXED** — added `test_action_predict_empty_trajectory_fails_typed_no_artifact` (covers `[]`/`None`/non-list) and `test_action_predict_failed_poll_fails_typed_no_artifact`. Omni-work suite now 29 tests, green. |
| 3 | Medium | architecture (maintainability) | `client.py` `run_action_job` vs `run_video_job` | The ~17-line submit+poll loop (timeout guard, non-200, `parse_status`/failed, progress ramp, `DELETE`-on-timeout, R-14) is duplicated between the two functions; a future fix to the orphan-prevention/progress logic must be made twice and can drift. | **DEFERRED (recorded debt).** The clean fix (`_submit_and_poll(...) -> completed body` shared by both) requires editing `run_video_job` — the **proven t2v/i2v/t2v_audio path** — at close-out of a high-risk session; that expands the change surface into a GPU-verified generation path AM-S3 does not otherwise touch. Not a correctness defect (both paths tested). Left for a focused follow-up (noted in handoff). |
| 4 | Low | architecture (duplication) | `client.py` `action_resolved_params`/`build_action_form` vs the FD pair | The recipe-param body + form builder are near-identical to `fd_resolved_params`/`build_fd_form`. | **DEFERRED / accepted.** The divergence is meaningful (no input `action` array; `raw_action_dim` derived from the embodiment vs. measured; added `view_point`), and the two-source-of-truth split is the file's established pattern. The readability reviewer explicitly argued against merging (would blur two genuinely different request shapes). Accepted as-is. |

## Cleared on review (no finding)
- **INV-8** — `git diff --exit-code schemas/openapi.json` clean; the ID/policy artifact/trajectory
  contract matches the reference `gen_worker._encode_action_reply` + `jobs_router` (`get_trajectory`,
  `trajectory_url`) the WebUI action tab targets. Public shape unchanged.
- **INV-4** — no BF16 base default reachable from the default deployment (`DEFAULT_BASE_ACTION_DIR`
  removed; `from_env` → `None`; graft resolves to the quantized checkpoint; `.env.example` retired the
  default; the default engine `vllm_omni_work` never touches the loader). Only the AM-S2 reasoner + the
  labeled LEGACY reasoning overlay retain `/models/base` (out of scope; AM-S4).
- **INV-5** — action stays on `Plane.GENERATION` (`_plane_for_mode` unchanged); rides the resident omni
  model; no new plane, no co-residency claim. VRAM 14.3 GiB (P2).
- **Trust boundary** — conditioning (image_path/video_path) re-resolved via `resolve_within` before any
  submit; `_read_filepart(path, kind)` enforces the per-kind byte cap (video vs image) before the full read.
- **Blast radius** — all six changed files are in `blast_radius.allowed_files`; no forbidden file touched.

## Outcome
No Critical/High findings. One Medium correctness item (#1) **fixed** with regression tests (#2). Two
maintainability items (#3 Medium, #4 Low) recorded and **deferred** with rationale (avoid refactoring the
proven video path at close-out). Post-fix: omni-work suite 29 green; full CPU suite green (exit 0);
`openapi.json` clean.
