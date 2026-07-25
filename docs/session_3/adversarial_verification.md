# AM-S3 Adversarial Verification

Date: 2026-07-25 · Session: AM-S3 · Gate: `GATE-AM-S3-ACTION`. Fresh-context verifier (did not write the
code, did not review it); saw only the contracts, diff, and evidence; job = falsify the done condition
(`docs/agent_workflow/prompts/adversarial_verifier.md`). **VERDICT: PASS** (with the two owner/close-out
items the contract itself leaves open, correctly open).

## Deterministic checks (re-run independently — all green)
- `uv run pytest -m "not gpu"` → EXIT 0 (summary suppressed in this env; exit code is the signal).
- `uv run pytest tests/checkpoint_prep -q` → EXIT 0.
- `git diff --exit-code schemas/openapi.json` → clean (INV-8).
- `docker compose --env-file .env.example -f deploy/docker-compose.fp8.yml config` → EXIT 0; mounts **only**
  `/models/checkpoint` (quantized FP8) for api / vllm-omni / vllm-reasoner; **no `/models/base`, no BF16
  action mount** (INV-4).

## Disproven claims: NONE
Every load-bearing sub-claim survived:
- **INV-4** — the default action path (`vllm_omni_work`, `COSMOS3_GEN_ENGINE=vllm_omni`) never touches the
  loader; `loader.py` has no BF16 default (`from_env` → `None`; `DEFAULT_BASE_ACTION_DIR` removed, no
  lingering refs). Only the LEGACY reasoning overlay retains `/models/base` (out of AM-S3 scope).
- **INV-8** — `openapi.json` byte-clean; `jobs_router.py`/`routes/action.py`/`orchestrator/**` unmodified;
  the trajectory rides the pre-existing `/v1/jobs/{id}/trajectory` + `Job.trajectory_url` (no new shape).
- **INV-5** — `_plane_for_mode` unchanged → action on `Plane.GENERATION`; no new plane; VRAM trace recorded.
- **INV-6** — `OWNER-AM-ACTION-QUALITY` recorded **PENDING**; no false "verified" for action anywhere.
- **INV-2** — t2i re-run at the deployed checkpoint (P2, valid PNG); the t2i code path is byte-unchanged.
- **Blast radius** — all changed files in `allowed_files`; no forbidden file touched.
- **Tests** — assert real behavior (endpoint, embodiment-derived `raw_action_dim`, artifact type+content,
  no-partial-artifact-on-failure across degenerate/missing/empty/failed cases); not tautological.
- **adversarial_cases** — none live (no re-export → R-10 N/A; no silent BF16 read; collision path still
  raises; empty-trajectory case fixed per sharded Finding 1).
- **Code ↔ evidence** — the async submit→poll→read-`action`→conditional-`/content` wiring matches P1/P2 and
  mirrors the reference `gen_worker._encode_action_reply` the WebUI targets. GPU runs asserted with
  recorded evidence (P1/P2); verifier could not re-run them but found no reason the code would not produce them.

## Unsupported / incomplete (non-fatal, = the still-open close-out)
The phase-level docs (`model_setup.md`, `evidence_map.md`, `handoff.md`, `eval_seed_cases.md`,
`risk_register.md`) were unchanged at verification time — still describing action as "GPU-unverified (S8)"
via the in-process graft + BF16 base. The verifier ruled this **does not falsify** the done condition: it
is *under*-claiming (opposite of an INV-6/INV-7 over-claim), no acceptance criterion requires those files
finalized, and the `model_setup.md` re-export recording is gated on a re-export that did not occur (E-06
refuted). It is the session's own pending close-out step + the owner's PENDING quality signature.
→ **Addressed in the close-out** (this session's final step): evidence_map / risk_register / model_setup /
eval_seed_cases / handoff reconciled to the AM-S3 as-built state.

## Verdict
**PASS** — every CPU-checkable invariant holds, the diff is inside the blast radius, the tests catch
regressions, and the code is consistent with the recorded GPU evidence. Remaining (contract-permitted)
open items: the owner's `OWNER-AM-ACTION-QUALITY` signature (recorded PENDING) and the close-out doc
reconciliation (done as the final step).

> **Post-verification update (2026-07-25):** both previously-open items are now closed —
> `OWNER-AM-ACTION-QUALITY` has since been signed **PASS** by the owner (Feng; all three v1-scope modes
> judged good in the Action tab), and the close-out docs are reconciled. **`GATE-AM-S3-ACTION` fully
> PASSES.** (The findings above are the verifier's original, point-in-time record and are left intact.)
