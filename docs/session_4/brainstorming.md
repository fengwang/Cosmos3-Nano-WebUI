# UX-S4 Brainstorming — README / Docs Friendliness

Date: 2026-07-16
Risk: low · Routing: single_agent (single agent + deterministic checks + one review)
Authority: `docs/session_4_contract.yaml`, `docs/project_contract.md`, PRD §3.7/§4 FR-9.

## Context Explored

- **Repo state:** clean tree on `phase3-session-4`; UX-S1/S2/S3 are closed and
  committed on this branch's ancestry. Auth is fully removed
  (`rg --hidden "COSMOS3_API_KEY|X-API-Key|require_api_key|UnauthorizedError"`
  clean outside `docs/`), and no auth prose survives in `README.md`/`SECURITY.md`
  (R-09 re-verify: nothing to remove).
- **README today** (`README.md`): interleaves a user quickstart with a
  duplicated dev/CI "Development" section (`:132-150`), a long "Limitations &
  beta status" section (`:152-180`), a prominent `[!WARNING]` beta banner, and a
  dangling "Release readiness → `docs/release_checklist.md`" link (`:202`, now at
  `docs/archive/phase-2/`). E-12 / R-08.
- **CONTRIBUTING.md already exists** and already owns most of the dev/CI workflow
  (uv sync, ruff, pytest, pnpm gen:api/build/lint/typecheck/test, PR guidelines).
  So relocation is mostly **de-duplication** (delete the README copy), not a
  move-from-scratch — this is the antidote to the "CONTRIBUTING duplicates rather
  than owns" failure mode the contract flags.
- **SECURITY.md** already reflects no-auth/loopback/socket (UX-S1 touched the
  auth lines), but line 55 still points at `(R-16)` — a deferred/archived risk;
  the live phase-3 risk carrying it forward is **R-01**.
- **`webui/app/layout.tsx`** (the one non-doc file in the blast radius) carries
  stale "Session 8" (`:12` `metadata.description`) and "S9" (`:37` comment) copy
  — flagged by the UX-S3 handoff as UX-S4's to fix.
- **Settled facts to reflect (UX-S2 evidence):** no auth to configure; curated
  negative-prompt default (good output out of the box); 720p (1280×720) is the
  **video** default served only by FP8/NVFP4 (peaks: FP8 14,665 MiB, NVFP4
  18,517 MiB, both < 32 GB) with a **guardrails-off** serving posture baked into
  compose. t2i is GPU-verified; other GPU paths remain a manual gate (MIG-S8).
- **Make targets / env vars verified for a runnable quickstart:** `make build`,
  `make up-fp8`, `make up-nvfp4`, `make health` (→ `GET /v1/health/ready`);
  `BIND_ADDR=127.0.0.1` default; host download dir `COSMOS3_FP8_DIR`, in-container
  `COSMOS3_MODEL_DIR`; the pinned FP8 download command lives in `.env.example`.

## Confirmed Decisions (interview, 2026-07-16)

| # | Decision | Chosen | Rejected |
|---|---|---|---|
| Q1 | Verification depth for a low-risk session | **Full treatment** — full refining pack + deterministic checks + 6-axis sharded review + fresh-context adversarial verifier (matches the UX-S3 precedent) | Streamlined (one review); Minimal (self-review only) |
| Q2 | Tone / where caveats live | **Relaxed; caveats consolidated into one slim "Status & security" section at the end**, with a light one-line trusted-LAN pointer up top | Honesty banner in the first screenful; keep the prominent beta WARNING |
| Q3 | Two dangling references | **Drop** the README "Release readiness" bullet; **repoint** SECURITY.md `(R-16)` → live **R-01** | Repoint both to archive; drop both entirely |
| — | README structure | **Approach A — task-first funnel** (What → Features → Quickstart → Requirements → Checkpoints → Troubleshooting → Status & security → project links) | B: quickstart-first; C: two-audience split in README |

Low-stakes defaults confirmed: keep a slim **Troubleshooting** section in README;
`layout.tsx` `description` mirrors the subtitle (drop "Session 8"); soften the
status **badge** wording but keep it honest.

## Approaches Considered (README structure)

- **A — Task-first funnel (chosen).** A newcomer reads *what it is*, sees the
  *feature/verification table*, then follows a *runnable ~5-min quickstart*;
  operational help (Troubleshooting) and the honest caveats (Status & security)
  come after the happy path. De-duplicates dev/CI out to CONTRIBUTING. Best fit
  for "features-first, few-minute on-ramp" (FR-9) with "tone relaxed, honesty
  retained" (PRD §3.2).
- **B — Quickstart-first.** Lead with the quickstart immediately. Rejected: asks
  a reader to clone before they know what the project does; the feature/status
  table is the honesty surface and should precede the run steps.
- **C — Two-audience split inside README.** Rejected: pulls contributor content
  back into README, directly fighting the CONTRIBUTING relocation goal (FR-9) and
  the "CONTRIBUTING owns dev/CI" failure-mode guard.

## Validated Design (approved 2026-07-16)

**`README.md` (Approach A outline)** — see `design.md` D1 for section-by-section
content and where each contract clause lands.

**`CONTRIBUTING.md`** — becomes the *sole* owner of dev/CI: fold in the README's
remaining bits (`uv python install 3.12`, the "mirrors the CPU-only CI" framing),
then the README "Development" section is deleted (moved, not lost, not duplicated).

**`SECURITY.md`** — repoint `(R-16)` → live **R-01**; keep the honest
no-auth/loopback/socket notes; add one honest line on the **guardrails-off**
generation default (safety-relevant, per the UX-S2 handoff).

**`webui/app/layout.tsx`** — `metadata.description` mirrors the README subtitle
(drop "Session 8"); the `(used from S9)` comment becomes generic.

## Design-for-clarity notes

- **One honesty surface.** All caveats live in exactly one README section
  ("Status & security") plus `SECURITY.md`; the Features table carries only the
  terse per-mode status. No caveat is stated in three places to drift out of sync
  (the "per-mode claims drifting ahead of evidence_map" failure mode).
- **CONTRIBUTING is the single source of truth for dev/CI.** README references it;
  it does not restate the commands. One owner, one place to update.
- **`docs/model_setup.md` stays the source of truth** for checkpoint facts; README
  shows a snapshot table and points there (no substance edit to model_setup).

## Non-Goals (from contract)

- Any code/config/WebUI behavior change beyond the `layout.tsx` copy fix
  (UX-S1/S2/S3 own their surfaces).
- Reintroducing auth prose UX-S1 removed (re-verify none remains).
- Editing `docs/archive/**` or the substance of `docs/model_setup.md`.
- Marketing copy, screenshots/images, or a new site.
