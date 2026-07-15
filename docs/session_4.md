# Session 4 (UX-S4) - README / Docs Friendliness

Contract: `docs/session_4_contract.yaml`
Risk: low
Routing: single_agent (single agent + deterministic checks + one review)

## Objective

Make `README.md` user-first: lead with features and a quickstart a new user
can follow in a few minutes, relocate development/CI detail into
`CONTRIBUTING.md`, keep a slim honest security/status callout, and leave every
internal link resolving. Run last, on the settled post-`UX-S1`/`UX-S2`/`UX-S3`
state.

## Why This Session Exists

The current README interleaves a user quickstart with development/CI commands
and a long limitations section, and now links to a doc that moved to the
archive (`docs/evidence_map.md` E-12). It reads as a contributor document, not
a user's few-minute on-ramp. This session reframes it for the trusted-LAN
appliance posture while keeping the project honest. It runs last so it rewrites
on the state left by auth removal (`UX-S1`), the new defaults (`UX-S2`), and
the decluttered UI (`UX-S3`) — avoiding the shared-prose conflict `R-09`.

## In Scope

1. Restructure `README.md` to lead with **what it does** (features) and a
   **~5-minute quickstart** (clone → download a checkpoint → `make build` →
   `make up-fp8` → `make health` → open the Studio), reflecting the post-`UX-S1`
   no-auth flow and the post-`UX-S2` defaults (good output out of the box; 720p
   video default with its VRAM advisory for FP8/NVFP4).
2. Relocate the development/CI workflow (`uv sync`, `ruff`, `pytest`, `pnpm
   build/lint/typecheck/test`, the CI mirror) from `README.md` into
   `CONTRIBUTING.md`.
3. Keep a **slim honest** security/status callout: no auth, trusted-LAN
   assumption, loopback default (LAN is an explicit opt-in), root-equivalent
   Docker socket; and the honest per-mode verification status (t2i
   GPU-verified; other modes / the 720p video default carry the recommended
   smoke evidence or a manual-gate note).
4. Tighten "Checkpoint setup" to the essentials with a pointer to
   `docs/model_setup.md` for depth.
5. Fix every dangling internal link: repoint or drop the
   `docs/release_checklist.md` reference (now archived) and the `SECURITY.md`
   `R-16` pointer (archived phase-1); update `SECURITY.md` deployment notes to
   the no-auth posture.

## Out of Scope

- Any code, config, or WebUI change (`UX-S1`/`UX-S2`/`UX-S3`).
- Reintroducing auth prose that `UX-S1` removed (re-verify none remains).
- Editing `docs/archive/**` or `docs/model_setup.md`'s substance beyond link
  correctness.
- Publishing images, marketing copy, or a new site.

## Deliverables

- A features-first `README.md` with a few-minute quickstart, no development/CI
  clutter, and a slim honest status/security callout.
- `CONTRIBUTING.md` carrying the relocated development/CI workflow.
- `SECURITY.md` reflecting the no-auth + trusted-LAN + socket posture.
- Every internal doc link resolving (no archived/dead references).

## Deterministic Checks

```bash
rg -n "release_checklist|R-16" README.md SECURITY.md   # expect: none, or repointed
# verify every relative link in README.md / SECURITY.md / CONTRIBUTING.md resolves to a real file
rg -n "COSMOS3_API_KEY|X-API-Key" README.md SECURITY.md   # expect: none (auth removed in UX-S1)
```

## Exit Criteria

- `GATE-UX-S4-DOCS` passes.
- README is features-first with a quickstart a new user can follow in minutes;
  dev/CI detail lives in `CONTRIBUTING.md`.
- A slim honest security/status callout is present and accurate.
- Every internal doc link resolves; no `release_checklist.md` or live `R-16`
  reference; no residual auth prose (`EV-UX-DOCS-LINKS-RESOLVE`).

## Handoff

Final phase deliverable: confirm `docs/risk_register.md`,
`docs/evidence_map.md`, and `docs/eval_seed_cases.md` reflect the closed state
of `UX-S1`..`UX-S4`, and record any residual item (e.g. `R-05` VRAM caveat,
deferred `R-16`) in the closing handoff.
