# PRD - UX Simplification and Trusted-LAN Appliance Posture

Date: 2026-07-15
Status: Draft blueprint (revised after adversarial review), documentation first
Owner: Feng
Related: `docs/project_contract.md`, `docs/evidence_map.md`,
`docs/risk_register.md`, `docs/eval_seed_cases.md`,
`docs/session_{1..4}.md`, `docs/session_{1..4}_contract.yaml`. Prior phases
are archived under `docs/archive/phase-1/` (migration, `MIG-S*`) and
`docs/archive/phase-2/` (GPU release readiness, `GPU-S*`); they are the
deep-study input to this blueprint and are not edited by this phase.

## 1. Problem

Cosmos3-Nano-WebUI shipped as a public beta with GPU text-to-image verified
end to end (`docs/archive/phase-2/`), but its first-run experience is shaped
for a cautious public preview rather than for the way it is actually
deployed: a single machine on a trusted LAN, driven by one user or a small
team. Four kinds of friction get in the way of a fast, pleasant first run:

- **Auth configuration overhead.** The API ships an optional `X-API-Key`
  gate (`COSMOS3_API_KEY`); the WebUI BFF forwards it. On a trusted LAN this
  is pure configuration ceremony that every operator must reason about,
  disable, or wire through, for no benefit (`api/app/auth.py`;
  `api/app/main.py:211`; `webui/lib/proxy.ts:39`).
- **Quality defaults are not preset.** The model ships a curated negative
  prompt (`assets/negative_prompt.json`, a 15 KB structured object) and can
  generate at 720p, but the API applies neither by default: `negative_prompt`
  has no default and nothing loads the file at runtime (`api/app/schemas.py:95`),
  and the server default resolution is 480 (`api/engines/vllm_omni/client.py:78`).
  A new user must discover and set both to get the intended output quality.
- **The WebUI carries a developer artifact.** The `/gallery` route is a
  design-system component showcase (`webui/app/gallery/page.tsx`) surfaced as
  a primary nav item (`webui/app/_components/PrimaryNav.tsx:14`); the home
  page is a stale stub whose only content links to it (`webui/app/page.tsx:10`).
  The generated-media viewport is also small for a media tool
  (`webui/components/MediaPreview.module.css` caps it at `60vh` inside a
  `60rem` studio column).
- **The README is written for contributors, not users.** It interleaves a
  user quickstart with development/CI commands and a long limitations section
  (`README.md`), and now contains at least one dangling link to a doc that
  moved to the archive (`docs/release_checklist.md`).

None of this is a defect. It is a product-posture mismatch: the project is
tuned for "cautious public preview" when its real use is "low-friction
trusted-LAN appliance."

## 2. Goal

Reshape Cosmos3-Nano-WebUI's configuration and first-run UX for a trusted-LAN
deployment while keeping it an honest, still-public open-source project.
Concretely: remove API-key auth entirely; preset the curated negative prompt
and a 720p video default so good output is the zero-configuration default;
declutter the WebUI (drop the component gallery, land users on the Studio,
enlarge the media viewport); and rewrite the README to lead with features and
a few-minute quickstart, relocating developer detail to `CONTRIBUTING.md`
while retaining a slim, honest security/status note.

This is a documentation-and-blueprint pass only. It defines the sessions,
contracts, and gates that later development sessions execute one at a time; it
does not itself change application code, configuration, or documentation
content beyond the blueprint documents in `docs/`.

## 3. Owner Decisions

These decisions are binding for this blueprint and the sessions it defines.
They were fixed with the owner during the interview that produced this
blueprint (2026-07-15).

1. Session IDs are `UX-S1` through `UX-S4`. Deliverables are written at
   `docs/` root (prior phases are already archived); numbering is fresh 1..4.
2. **Posture:** the repository stays a public open-source project, but its
   intended deployment is an explicitly trusted LAN / lab machine. The README
   and `SECURITY.md` keep a slimmed but honest note that there is no auth and
   the deployment assumes a trusted network — tone relaxed, honesty retained.
3. **Auth is removed, not merely defaulted off.** The `X-API-Key` mechanism
   and its `COSMOS3_API_KEY` configuration are deleted from the API, the WebUI
   BFF, config files, tests, and docs. Removing auth does **not** change the
   default network binding: published ports stay on loopback
   (`BIND_ADDR=127.0.0.1`) and LAN exposure remains an explicit operator
   opt-in.
4. **Negative-prompt preset** is applied server-side as an overridable default:
   when a request omits `negative_prompt`, the API loads the curated file and
   passes it to the engine; the WebUI shows a "using recommended default"
   placeholder; a user-supplied value overrides it. The file path is resolved
   from the configurable model-directory environment variable, never a
   hardcoded absolute path (INV-1). The exact structured-JSON-vs-string wiring
   is a `UX-S2` design decision, not fixed here.
5. **Resolution preset:** 720p (1280×720) becomes the default for **video**
   modes (`t2v`/`i2v`/`t2v_audio`) at both the API server layer and the WebUI
   default preset. The resolution picker/presets remain available; text→image
   defaults are unchanged. 720p video is served only by the quantized
   FP8/NVFP4 generation path, which fits 32 GB (existing bundled 720p example
   artifacts and a VRAM trace, `docs/evidence_map.md`), never the BF16 base,
   which does not.
6. **Component Gallery** is fully removed (route, nav item, and home-page
   link); the home route `/` redirects to / becomes the Studio. The generated
   media viewport is enlarged (wider container, taller media) without a
   structural redesign of the studio.
7. **README** leads with features + a ~5-minute quickstart; development/CI
   detail moves into `CONTRIBUTING.md`; a slim honest status/security callout
   and the essential checkpoint-setup steps remain, with depth deferred to
   `docs/model_setup.md`.
8. **GPU validation posture:** CPU tests + WebUI build/lint/typecheck + docs
   are the blocking exit criteria for every session. GPU validation of the new
   generation defaults is a **recommended, human-decision-gated (non-blocking)**
   5090 smoke in `UX-S2`, folded into the existing manual GPU gate — not an
   auto-blocking gate.
9. **Sequencing:** sessions are largely independent, but `UX-S4` (docs) runs
   **last** so it rewrites on the settled post-`UX-S1` state.
   `UX-S1` edits only the auth-specific lines of `README.md`/`SECURITY.md`; the
   broad README restructure belongs to `UX-S4`.

## 4. Requirements

Requirement keywords follow RFC 2119. A claim not yet verified at blueprint
time is written as a verification task or session gate, not a shipped
capability.

### Functional

- **FR-1 (MUST)** `UX-S1` removes the `X-API-Key`/`COSMOS3_API_KEY` auth path
  entirely — the FastAPI dependency and its wiring (`api/app/auth.py`;
  `api/app/main.py:19,211,215-226`), the `UnauthorizedError`→401 handler
  (`api/app/errors.py`), the WebUI BFF key injection
  (`webui/lib/proxy.ts:39`, `webui/lib/proxyFetch.ts:30`), the
  `COSMOS3_API_KEY` config entries (`.env`, `.env.example`,
  `deploy/docker-compose.base.yml`), and all auth-specific tests — leaving no
  dangling reference anywhere in the tracked tree (verified by a
  whole-repository `rg --hidden` sweep).
- **FR-2 (MUST)** After `UX-S1`, `schemas/openapi.json` is **regenerated from
  code** (never hand-edited) and contains no `x-api-key` parameter or security
  scheme; `tests/test_openapi.py` passes.
- **FR-3 (MUST)** Health (`/v1/health/{live,ready}`) and metrics
  (`/v1/metrics`) remain reachable and behaviorally unchanged after auth
  removal; the Docker healthcheck keeps working.
- **FR-4 (MUST)** `UX-S2` applies the curated negative prompt as an
  overridable server-side default when a request omits `negative_prompt`;
  a user-supplied value still overrides it; the WebUI shows a "using
  recommended default" affordance. The file path is derived from the
  configurable model-directory environment variable; a missing file degrades
  gracefully (generation proceeds without a negative prompt, logged) rather
  than crashing.
- **FR-5 (MUST)** `UX-S2` makes 1280×720 the default for `t2v`/`i2v`/`t2v_audio`
  at both the API server default and the WebUI default preset, without
  changing the text→image default, and keeps the resolution picker/presets
  available.
- **FR-6 (SHOULD)** `UX-S2` records a 5090 smoke that the shipped 720p video
  default generates a valid artifact within 32 GB for FP8 **and** NVFP4 at the
  shipped frame count, noting the guardrails posture used. If infeasible in
  the session's hardware budget, it records why and routes to the manual GPU
  gate rather than dropping silently.
- **FR-7 (MUST)** `UX-S3` removes the `/gallery` route, its nav item, and the
  home-page link, and makes `/` render or redirect to the Studio, leaving no
  dead route or dead link (`rg -i gallery` clean in `webui/app`/`webui/components`
  apart from unrelated history wording).
- **FR-8 (MUST)** `UX-S3` enlarges the generated-media viewport (increase
  `MediaPreview` max-height and the studio container max-width relative to the
  `60vh`/`60rem` baseline) while keeping the layout responsive and the
  compare-grid intact.
- **FR-9 (MUST)** `UX-S4` restructures `README.md` to lead with features and a
  quickstart a new user can follow in a few minutes, relocates the
  development/CI workflow into `CONTRIBUTING.md`, retains a slim honest
  security/status callout, and leaves every internal link resolving (no
  reference to the archived `docs/release_checklist.md`, no live `R-16`).
- **FR-10 (MUST)** No session changes any public API request/response **schema
  shape** other than the removal of the `X-API-Key` parameter; presets change
  defaults, not shapes.

### Non-Functional

- **NFR-1 (MUST)** No secret, token, private host, private absolute path, or
  model weight is committed to this repository as part of this work. In
  particular, the negative-prompt file is referenced via a configurable
  model-directory variable, not a baked-in absolute path.
- **NFR-2 (MUST)** Removing auth introduces no new capability and no behavior
  regression beyond dropping the `X-API-Key` gate; the API's Docker-socket
  controller surface is unchanged, and the trusted-LAN assumption plus the
  root-equivalent socket risk are documented, not silently accepted (R-01).
- **NFR-3 (MUST)** Every release-affecting recommendation in
  `docs/project_contract.md` has an evidence row in `docs/evidence_map.md` or
  is marked speculative with a named re-verification gate.
- **NFR-4 (SHOULD)** Every manual GPU smoke records hardware, driver/CUDA
  context, checkpoint repo and revision, request shape (dims/frames/fps/steps/seed),
  peak VRAM, guardrails posture, artifact metadata, and pass/fail result.
- **NFR-5 (MUST)** Each session's blocking exit criteria are deterministic
  (CPU tests, WebUI build/lint/typecheck/test, `rg` sweeps, regenerated
  OpenAPI diff); GPU smokes are recommended, non-blocking, human-gated.

## 5. Acceptance Criteria

This blueprint's scope is done only when all are true:

1. `docs/prd.md`, `docs/project_contract.md`, `docs/evidence_map.md`,
   `docs/risk_register.md`, and `docs/eval_seed_cases.md` exist in their
   phase-3 form, and `docs/session_{1..4}.md` /
   `docs/session_{1..4}_contract.yaml` exist for `UX-S1`..`UX-S4`.
2. Each session document defines objective, in-scope, out-of-scope,
   deliverables, and exit criteria, and references the repository evidence and
   the archived deep-study docs it depends on.
3. Each session contract classifies risk, routes per the risk router, and
   fixes a blast radius (allowed/forbidden files), invariants, deterministic
   checks, adversarial cases, and a done condition.
4. `docs/evidence_map.md` carries a row for every major recommendation, with
   speculative claims marked and never promoted to MUST.
5. The contract pack survives a second, adversarial compilation pass: the
   720p-vs-VRAM contradiction, the negative-prompt absolute-path hazard, the
   auth/socket coupling, and the S1/S4 doc overlap are each resolved in the
   text rather than left latent.
6. No application code, configuration, or non-`docs/` content is modified by
   this pass.

## 6. Non-Goals

- Writing or editing any application code, configuration, Dockerfile, WebUI,
  or non-`docs/` content during this blueprint pass. This PRD and its
  companions define sessions; they do not execute them.
- Changing the default network binding to non-loopback, adding TLS, or adding
  any replacement authentication/authorization mechanism. Auth is removed;
  LAN exposure stays an explicit operator opt-in.
- Hardening the Docker-socket privilege (archived `R-16`); it stays a
  documented residual risk, not a work item this phase.
- Full GPU validation of every generation mode, or any guardrails-on GPU run.
  Only the recommended 720p video smoke (FP8/NVFP4) in `UX-S2` is in scope,
  and it is non-blocking.
- Changing checkpoint revisions, the vLLM-Omni pin, or anything in
  `docs/archive/**`.
- A structural redesign of the Studio, a new landing/marketing page beyond a
  redirect to the Studio, or a design-system overhaul.

## 7. Session Plan

| # | Session | Risk | Primary gate |
|---|---|---|---|
| 1 | Remove API-key auth (API + WebUI + config + tests + auth-doc lines) | high | `GATE-UX-S1-AUTH` |
| 2 | Generation defaults: negative-prompt file preset + 720p video default | medium | `GATE-UX-S2-DEFAULTS` |
| 3 | WebUI declutter: remove gallery, land on Studio, enlarge media viewport | low | `GATE-UX-S3-WEBUI` |
| 4 | README/docs friendliness: features-first README + CONTRIBUTING relocation | low | `GATE-UX-S4-DOCS` |
