# UX-S4 Design — README / Docs Friendliness

Date: 2026-07-16
Source: `docs/session_4/proposal.md`; authority `docs/session_4_contract.yaml`.

## Context

Final phase-3 session. Docs-only (plus one allowed `layout.tsx` copy fix). The
"how" here is prose architecture: how the README is sectioned, where each
contract clause is satisfied, and how honesty is kept in exactly one place so it
cannot drift.

## Goals / Non-Goals

- **Goals:** features-first README with a runnable ~5-min quickstart; dev/CI
  owned by `CONTRIBUTING.md`; one slim honest Status & security section; every
  internal link resolves; stale `layout.tsx` copy corrected.
- **Non-Goals:** code/behavior change (beyond `layout.tsx` copy); archive edits;
  `model_setup.md` substance; marketing/images/site; reintroducing auth.

## Decisions

### D1 — README section outline (Approach A, task-first funnel)

Order and per-section intent (→ marks the contract clause satisfied):

1. **Header** — logo + badges. Soften `status: beta / research preview` →
   `status: local self-hosted preview` (honest, calmer). Keep license/python/CI
   badges. → tone relaxed (PRD §3.2).
2. **Title + subtitle** — keep the current subtitle (accurate one-liner).
3. **Trusted-LAN pointer** — a single `> [!NOTE]` line: built for a trusted LAN,
   no app-layer auth, loopback default; "full status → Status & security". →
   INV-4 documented, not front-loaded as fear.
4. **What it does** — 2–3 sentences (tightened "What is this?"): local, single
   RTX 5090-class GPU, public quantized checkpoints, generation container.
5. **Features** — the capability/endpoint/**status** table. Honest per-mode:
   t2i (FP8/NVFP4) **GPU-verified**; t2v/i2v/t2v_audio/reason/action *implemented
   + CPU-tested, GPU = manual gate (MIG-S8)*; jobs/health/metrics/WebUI
   *CPU-tested*. → FR-9 honesty; no claim ahead of `evidence_map.md`.
6. **Quickstart (~5 min)** — `git clone` → `hf download` the pinned FP8 checkpoint
   → `cp .env.example .env` (optional) → `make build` → `make up-fp8` →
   `make health` → open `http://localhost:3000`. Callouts: *no auth to
   configure*; *defaults already give recommended quality (curated negative
   prompt) and 720p video* (UX-S2). The vLLM-Omni GPU build remains the manual
   gate (`[!NOTE]`). → FR-9 runnable quickstart; reflects UX-S1/S2.
7. **Requirements** — brief HW/SW (Linux + NVIDIA GPU; Docker + Compose; Python
   3.12 + uv, Node 22 + pnpm *for development*; disk per checkpoint).
8. **Checkpoint setup** — tightened: the 3-row repo/rev/license table + "serve
   exactly one of FP8/NVFP4" + `docs/model_setup.md` as **source of truth** +
   the model-license note. → in-scope item 4; no model_setup substance edit.
9. **Troubleshooting** — kept slim, user-facing (env-file discovery, LAN reach,
   one-stack-at-a-time, cold start). → user ops help; not dev/CI.
10. **Status & security** — the single honest callout. Contains: (a) per-mode
    verification status with a pointer to `docs/evidence_map.md`; (b) **no
    app-layer auth**, trusted-LAN assumption, **loopback default** (LAN = explicit
    opt-in), **root-equivalent Docker socket**; (c) **guardrails-off** generation
    posture (UX-S2, E-19); (d) 720p video served by **FP8/NVFP4** (not BF16) with
    the thin-FP8-headroom advisory (R-05); pointer to `SECURITY.md`. → FR-9
    slim honest callout; INV-4.
11. **Project & contributing** — one line each: Contributing → `CONTRIBUTING.md`
    (dev/CI lives there), Security → `SECURITY.md`, Code of Conduct, License.
    **Drop** "Release readiness". → in-scope item 2 pointer + Q3 drop.

The former README "Development" section (`:132-150`) is **removed**; its content
is owned by `CONTRIBUTING.md`.

### D2 — CONTRIBUTING.md owns dev/CI (no duplication)

CONTRIBUTING already carries Development setup + "Checks to run before a PR"
(mirrors CI) + PR guidelines. Fold in the only README-unique bits: `uv python
install 3.12` and the explicit "these mirror the CPU-only CI in
`.github/workflows/ci.yml`" framing. README then references CONTRIBUTING rather
than restating commands. **Why:** one source of truth; a future CI change is
edited in one place. Tidy CONTRIBUTING's loose "the release checklist" prose
(archived) to point at the risk register / evidence instead.

### D3 — SECURITY.md: R-16 → R-01 + guardrails line

Replace `See docs/risk_register.md (R-16).` with a pointer to the live phase-3
**R-01** (socket-after-auth-removal; explicitly "carries forward archived R-16").
Add one honest sentence: generation ships with guardrails **off** by default
(required for the 720p video default to fit 32 GB — E-19), so outputs are
unfiltered; treat this as a trusted-LAN/local posture. Keep the section slim.
**Why:** the deterministic check wants no live `R-16` token; R-01 is the accurate
live reference; the guardrails-off default is safety-relevant and must be honest.

### D4 — layout.tsx copy

`metadata.description`: `"Neumorphic WebUI foundation + design system (Session
8)."` → a user-facing one-liner mirroring the README subtitle (e.g.
`"Self-hostable API + Web UI for the Cosmos3-Nano world model — video, image,
reasoning, and robot action, from quantized FP8/NVFP4 checkpoints."`). The
`{/* … used from S9. */}` comment → generic ("async job/stream status"). **Why:**
"Session 8/S9" is stale internal phase copy leaking into a shipped metadata
string; correcting it is copy-only (no behavior/layout change).

## Risks / Trade-offs

- **[Dropping a must-have quickstart step (R-08)]** → the quickstart keeps the
  full path (checkpoint download + `make build`/`up-fp8`/`health`); a
  deterministic "quickstart mentions each essential" check is part of the review;
  the adversarial verifier attacks runnability.
- **[Slimmed note becomes dishonest]** → the Status & security section is
  cross-checked line-by-line against `evidence_map.md`/`risk_register.md`; the
  adversarial verifier attacks for over-claiming (implying untested modes work)
  and for hidden posture (auth/socket/guardrails).
- **[CONTRIBUTING duplicates rather than owns]** → README keeps a *pointer*, not
  commands; a `rg` for the dev commands confirms they live only in CONTRIBUTING.
- **[layout.tsx edit breaks the webui build]** → run `pnpm build && pnpm lint &&
  pnpm typecheck && pnpm test` from `webui/` after the edit (copy-only, expected
  green).
- **[A "friendly" link dangles]** → a relative-link resolver runs over all three
  root docs before and after; every link must point at an existing file.

## Migration Plan

Docs edits are non-transactional and reversible via git. Order: (1) build the
checker; (2) README restructure; (3) CONTRIBUTING/SECURITY/layout; (4) full
checks; (5) sharded review → fix High/Critical; (6) adversarial verifier;
(7) close-out (evidence/risk/eval/handoff). No rollback plan needed beyond
`git restore`.

## Open Questions

None. Q1–Q3 + structure + low-stakes defaults are all confirmed (2026-07-16).
