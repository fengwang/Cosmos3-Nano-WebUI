# Project Contract - UX Simplification and Trusted-LAN Appliance Posture

Date: 2026-07-15
Status: Active blueprint (revised output of a two-pass compilation)

Compilation: two-pass. The first pass drafted from the owner's requirement
(2026-07-15), repository evidence gathered by direct inspection
(`api/app/auth.py`, `api/app/main.py`, `api/app/schemas.py`,
`webui/lib/**`, `webui/app/**`, `deploy/**`, `README.md`, `SECURITY.md`), and
the archived phase-1/phase-2 deep-study docs. The second pass, an independent
adversarial spec review, found and resolved four substantive issues that a
naive transcription of the requirement would have shipped:

1. **720p video vs 32 GB VRAM.** The requirement "preset video to 720p"
   contradicted the archived evidence that 720p video exceeds 32 GB on the
   RTX 5090 (`docs/archive/phase-2/prd.md:192`;
   `docs/archive/phase-1/session_8/outputs/gate_record.md:23`). Resolved: that
   ceiling is the **BF16** path; the deployed generation path is quantized
   FP8/NVFP4, which fits 720p (bundled example artifacts + a VRAM trace,
   `docs/evidence_map.md`). The default is scoped to the quantized generation
   path, the thin-FP8-headroom caveat is recorded as `R-05`, and `UX-S2`'s
   recommended smoke must confirm the shipped config.
2. **Negative-prompt absolute path.** The requirement named a specific
   absolute path (`/data/models/Cosmos3-Nano/assets/negative_prompt.json`).
   Baked in literally, that violates INV-1 (no private absolute paths) and
   breaks in-container (wrong mount). Resolved: the path is derived from the
   configurable model-directory variable, with graceful fallback.
3. **Auth removal on a socket-mounted API.** Removing auth removes the only
   application-layer access control from an API that mounts the
   root-equivalent host Docker socket (`SECURITY.md:52-55`). Resolved: the
   default binding stays loopback (LAN is opt-in), and the trusted-LAN
   assumption plus the socket risk become a MUST-document invariant (`INV-4`,
   `R-01`), not a silent acceptance.
4. **S1/S4 document overlap.** Both the auth-removal session and the README
   session touch `README.md`/`SECURITY.md`. Resolved: `UX-S1` edits only the
   auth-specific lines; the broad restructure is `UX-S4`, which runs last on
   the settled state (Change Control §6).

This document is the revised output only.

Authority chain: read this file before implementing any phase-3 session.
Session-specific authority comes from `docs/session_{n}_contract.yaml`. If a
session contract conflicts with this file, stop and record the conflict
before editing.

## 1. Objective

Make Cosmos3-Nano-WebUI a low-friction trusted-LAN appliance without turning
it into a black box: remove API-key auth, preset the curated negative prompt
and a 720p video default, declutter and enlarge the WebUI, and make the README
user-first — while keeping the project honest about its (now auth-free)
security posture and reproducible from public inputs.

## 2. Hard Commitments

1. **Session identity:** session contracts are `UX-S1` through `UX-S4`;
   deliverables live at `docs/` root.
2. **Documentation-only blueprint:** this pass writes only `docs/**`. No
   application code, config, or non-doc content is edited until a later
   session executes its contract.
3. **Auth is removed, binding is not loosened:** auth removal must not change
   the default port binding. `BIND_ADDR` stays `127.0.0.1` by default; LAN
   exposure is an explicit, documented operator opt-in.
4. **Presets are overridable defaults, never locks:** the negative-prompt and
   resolution presets set defaults that a request (API) or the UI can still
   override. No preset removes user choice.
5. **Configurable paths only:** any file the runtime loads for a preset is
   resolved from an existing operator-set environment variable, never a
   hardcoded absolute host path (INV-1).
6. **No schema-shape regression:** existing public API request/response shapes
   and WebUI behavior are unchanged except for the removal of the `X-API-Key`
   parameter and the changed default values; `schemas/openapi.json` is
   regenerated from code and stays in sync.
7. **Quantized-only 720p:** the 720p video default is served by the FP8/NVFP4
   generation path; the BF16 base is never the 720p video path.
8. **Archive boundary:** `docs/archive/**` is historical record and is not
   edited by phase-3 sessions.
9. **Docs last:** `UX-S4` runs after `UX-S1`; `UX-S1` limits its `README.md`/
   `SECURITY.md` edits to auth-specific lines so the two sessions do not
   contend for the same prose.

## 3. Invariants

- **INV-1:** No secret, token, private host, private absolute path, or model
  weight is committed to this repository. The negative-prompt file is
  referenced via a configurable model-directory variable, not a baked-in
  absolute path.
- **INV-2:** `/v1/health/{live,ready}` and `/v1/metrics` stay reachable and
  behaviorally unchanged after auth removal; the Docker healthcheck keeps
  working.
- **INV-3:** Auth removal adds no new capability and no behavior regression
  beyond dropping the `X-API-Key` gate; the Docker-socket controller's
  fixed-verb surface is unchanged.
- **INV-4:** The default published-port binding is loopback
  (`BIND_ADDR=127.0.0.1`); LAN exposure is an explicit operator opt-in. The
  trusted-LAN assumption and the root-equivalent Docker-socket risk are
  documented, not silently accepted.
- **INV-5:** Every preset (negative prompt, resolution) is an overridable
  default — per-request via the API and via the WebUI — never a hard lock.
- **INV-6:** No public API request/response schema shape changes except the
  removal of the `X-API-Key` parameter. `schemas/openapi.json` is regenerated
  from code (never hand-edited) and stays in sync, guarded by
  `tests/test_openapi.py`.
- **INV-7:** The WebUI keeps its same-origin BFF posture — the browser never
  calls the API directly; the proxy still forwards requests, minus any API-key
  injection.
- **INV-8:** The 720p video default is served only by the quantized FP8/NVFP4
  generation path (never the BF16 base, which exceeds 32 GB at 720p);
  generation surfaces a documented advisory rather than a silent OOM if a
  heavier-than-default config is requested.

## 4. Gates

- **GATE-UX-S1-AUTH:** the `X-API-Key`/`COSMOS3_API_KEY` path is removed from
  API, WebUI, config, tests, and auth-specific doc lines; a whole-repo
  `rg --hidden` sweep for the auth tokens is clean; `schemas/openapi.json` is
  regenerated with no `x-api-key`; the CPU suite and the WebUI
  build/lint/typecheck/test are green; health and metrics still respond.
- **GATE-UX-S2-DEFAULTS:** the curated negative prompt loads (from the
  configurable model-assets path, with graceful fallback) and applies as an
  overridable default; 1280×720 is the default for video at server + UI, with
  text→image unchanged and the picker intact; the CPU suite is green; the
  recommended FP8/NVFP4 720p 5090 smoke is recorded (pass, or a documented,
  owner-accepted deferral).
- **GATE-UX-S3-WEBUI:** the gallery route, nav item, and home link are gone;
  `/` renders/redirects to the Studio; the media viewport is enlarged; the
  WebUI build/lint/typecheck/test are green; no dead route or dead link
  remains.
- **GATE-UX-S4-DOCS:** `README.md` is features-first with a few-minute
  quickstart; development/CI detail lives in `CONTRIBUTING.md`; a slim honest
  security/status callout is present; every internal doc link resolves (no
  archived `release_checklist.md`, no live `R-16`); `SECURITY.md` reflects the
  no-auth + trusted-LAN + socket posture.

## 5. Session Routing

Risk classification follows the requested risk router.

| Session | Risk | Routing | Human gate |
|---|---|---|---|
| UX-S1 Remove auth | high | independent test writer + sharded review + adversarial verifier | Mandatory before merge — security posture change (auth removal on a socket-mounted API) |
| UX-S2 Generation defaults | medium | worker + sharded review + adversarial verifier | On the negative-prompt wiring decision, and to accept/defer the recommended 720p GPU smoke |
| UX-S3 WebUI declutter | low | single agent + deterministic checks + one review | None |
| UX-S4 README/docs | low | single agent + deterministic checks + one review | None |

High-risk sessions require deterministic checks, sharded review over the
review axes, adversarial verification of claims, and the named human gate
before the session's done condition is accepted. `UX-S1` is high because it
removes an access-control mechanism from a service that holds a
root-equivalent host capability; the routing favors an independent test
writer (so the removal is proven by tests written against the new contract,
not merely by deleting the old assertions) and a mandatory pre-merge human
decision.

## 6. Change Control

- Do not edit outside a session contract's `blast_radius.allowed_files`.
- Do not add model weights, generated media, caches, or bulky archives to the
  repository.
- Do not edit `docs/archive/**`.
- Do not change the default network binding, add TLS, or add a replacement
  auth mechanism as part of this work.
- Treat `README.md` and `SECURITY.md` as a shared surface between `UX-S1` and
  `UX-S4`: `UX-S1` edits only the auth-specific lines it must not leave
  dangling; the broad restructure is `UX-S4`, executed last.
- Do not change public API route shapes or request/response schemas; presets
  change default values only.
- Treat `schemas/openapi.json` as generated: never hand-edit it; regenerate
  from code and let `tests/test_openapi.py` guard the sync.

## 7. Verification Policy

- Classify failures before fixing: BUG, SPEC_GAP, AMBIGUITY, ENVIRONMENT, or
  TEST_BUG (`docs/agent_workflow/prompts/failure_arbiter.md`).
- Prefer deterministic evidence: `uv run pytest -m "not gpu"`; from `webui/`,
  `pnpm build && pnpm lint && pnpm typecheck && pnpm test`; `rg --hidden`
  sweeps for removed tokens and stale links; a regenerated-vs-committed
  `schemas/openapi.json` diff.
- GPU checks are manual, recommended, non-blocking gates. When run, record
  hardware, driver/CUDA context, checkpoint repo and revision, request shape,
  peak VRAM, guardrails posture, artifact metadata, and result (NFR-4).
- Claims in user-facing docs must point to an evidence row in
  `docs/evidence_map.md` or be phrased as a limitation.

## 8. Done Condition

The phase-3 blueprint's session set is done when `GATE-UX-S1-AUTH` through
`GATE-UX-S4-DOCS` all pass; the recommended `UX-S2` GPU smoke is either
recorded green or carries a documented, owner-accepted deferral; and
`docs/risk_register.md`, `docs/evidence_map.md`, and `docs/eval_seed_cases.md`
reflect the final state of every session that has closed, including any
archived risk (`R-16` socket hardening) a session touches or defers.
