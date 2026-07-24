# Project Contract - Single-GPU Comfort and ADHD-Friendly Onboarding

Date: 2026-07-24
Status: Active blueprint (revised output of a two-pass compilation)

Compilation: two-pass. The first pass drafted from the owner's requirement
(2026-07-24), repository evidence gathered by direct inspection
(`api/app/main.py`, `api/orchestrator/manager.py`, `api/jobs/gen_client.py`,
`api/engines/vllm_omni/work.py`, `api/app/routes/reasoning.py`,
`webui/app/(studio)/StudioProvider.tsx`, `deploy/**`, `.env.example`,
`README.md`), the archived phase-1/2/3 packs, and the three ADHD research
reports under `docs/adhd/`. The second pass, an independent adversarial spec
review, found and resolved six substantive issues that a naive transcription of
the requirement would have shipped:

1. **Wrong timeout / unserved goal.** "Raise the video-generation timeout
   10→30 min" taken literally targets a limit that does not exist at 10 min:
   generation is already bounded at 2400 s / 7200 s and cold start at 1800 s
   (`docs/evidence_map.md` E-03/E-04). The only 10-min default is the **idle
   keep-warm** timeout (`api/app/main.py:173`; E-01/E-02). Resolved: the change
   is scoped to `COSMOS3_IDLE_TIMEOUT_SECONDS` (600→1800), the framing is
   corrected in the PRD (§1.1) and evidence map, and the generation/cold-start
   ceilings are recorded as an audit, not a change.
2. **Idle-default drift (two sources of truth).** The idle default is defined
   both as the `main.py` env fallback (`"600"`) and as the `Orchestrator`
   constructor default (`600.0`, `api/orchestrator/manager.py:46`); production
   always passes the env value, but a directly-constructed orchestrator (tests,
   future callers) would silently keep 10 min (E-06). Resolved: both are in the
   `LX-S1` blast radius and both move to 1800; a unit test pins the app-wired
   default so the two cannot drift.
3. **README honesty regression under a "punchy hook."** The owner chose a
   punchier hook with caveats relocated to the bottom. A naive rewrite in that
   direction can over-claim (imply every mode is GPU-verified) or quietly drop
   a caveat — the exact false-claim class the phase-3 docs review caught
   (`docs/archive/phase-3/handoff.md`; that phase's E-26). Resolved: honesty is
   a hard invariant (`INV-6`) — the hook must be factually true, the per-mode
   verification status stays, the full caveats stay **visible** (not
   collapsed), nothing is deleted — and `LX-S2` carries a mandatory adversarial
   no-over-claim / no-lost-caveat pass despite being low risk.
4. **S1/S2 shared README surface.** The README references a timeout
   (`README.md:136`); if `LX-S1` edited the README to document the new default
   while `LX-S2` rewrote it, the two would contend (phase-3's `R-09`).
   Resolved: `LX-S1` does not touch `README.md`; `LX-S2` runs last and owns all
   README prose, documenting the settled 30-min behavior (Change Control §6).
5. **Report-vs-reality: Codespaces.** The Gemini report makes GitHub
   Codespaces / DevContainers a headline "zero-friction remote development"
   pillar; the other two reports are local-only (E-12). A local RTX 5090 is
   required and Codespaces provide no suitable GPU. Resolved: the recommendation
   is dropped, the disagreement is stated in the evidence map, and the README
   carries no cloud/Codespaces call to action.
6. **Report-vs-reality: typography as MUST.** Two reports give font /
   line-height / alignment specifications (E-14); these are unachievable and
   untestable inside a GitHub-rendered README (GitHub controls the typography).
   Resolved: typography recommendations are non-normative context; the README's
   readability requirements are structural (headings, chunking, whitespace,
   progressive disclosure, in-page navigation), which are testable.

This document is the revised output only.

Authority chain: read this file before implementing any phase-4 session.
Session-specific authority comes from `docs/session_{n}_contract.yaml`. If a
session contract conflicts with this file, stop and record the conflict before
editing.

## 1. Objective

Make a single RTX 5090 comfortable to run with default settings and give the
README a fast, low-friction on-ramp for a reader who skims — while keeping the
project honest about its (still auth-free, guardrails-off, single-GPU-verified)
posture and reproducible from public inputs. Deliver this as a documentation
blueprint: two session contracts and their gates, executed later one at a time.

## 2. Hard Commitments

1. **Session identity:** session contracts are `LX-S1` and `LX-S2`;
   deliverables live at `docs/` root. Gates are `GATE-LX-S1-TIMEOUT` and
   `GATE-LX-S2-README`.
2. **Documentation-only blueprint:** this pass writes only `docs/**`. No
   application code, config, or non-doc content is edited until a later
   session executes its contract.
3. **Idle keep-warm only:** the single timeout change is
   `COSMOS3_IDLE_TIMEOUT_SECONDS` 600→1800. The generation timeouts, the
   cold-start ceiling, the reasoner timeout, and the WebUI SSE heartbeat are
   **not** changed by this phase; they are audited and recorded.
4. **Default, not lock:** the idle keep-warm value stays operator-configurable
   through its existing environment variable; `0` still disables eviction. The
   phase changes the shipped default and surfaces the knob, nothing more.
5. **Honesty is preserved, not relaxed:** the README rewrite may change tone,
   order, and structure, but it may not delete, hide, or contradict any
   caveat, and it may not claim a capability the evidence does not support.
6. **Docs last, single owner:** `LX-S2` runs after `LX-S1`; `LX-S1` does not
   edit `README.md`, so the two sessions never contend for the same prose.
7. **No new remote-dev surface:** no Codespaces / DevContainer / cloud path is
   added; the project's supported deployment is local, on an RTX 5090.
8. **Single README:** the ADHD pass is structural on the one existing
   `README.md`; depth stays in the existing `CONTRIBUTING.md` /
   `docs/model_setup.md` (linked, not inlined). No new doc files, no site.
9. **Archive boundary:** `docs/archive/**` is historical record and is not
   edited by phase-4 sessions.
10. **No committed binaries:** the visual map is text (Mermaid); no image,
    model weight, or generated media is added (NFR-1).

## 3. Invariants

- **INV-1:** No secret, token, private host, private absolute path, model
  weight, or generated-media binary is committed as part of this work. The
  idle-timeout knob is an existing environment variable; no new absolute path
  is introduced.
- **INV-2:** The idle keep-warm value is an overridable operator setting, not a
  hard-coded lock; `COSMOS3_IDLE_TIMEOUT_SECONDS` still governs it and `0` still
  means "never evict" (the `notify_idle` contract in
  `api/orchestrator/manager.py` is unchanged).
- **INV-3:** `LX-S1` changes no public API request/response schema shape, no
  route behavior, and no other timeout; the only behavioral change is the idle
  eviction delay (10 → 30 min). `schemas/openapi.json` is unaffected.
- **INV-4:** Raising the idle keep-warm cannot starve a different plane:
  `Orchestrator.acquire` cancels any pending idle timer and evicts-before-load,
  so a request for another residency still preempts immediately regardless of
  the idle window (`api/orchestrator/manager.py` `acquire`/`_cancel_idle_timer`;
  `docs/evidence_map.md` E-05).
- **INV-5:** The README rewrite preserves the runnable quickstart: the pinned
  public-checkpoint download and the `make build` / `make up-fp8` /
  `make health` targets stay accurate against the `Makefile` and
  `docs/model_setup.md`; no setup step is dropped.
- **INV-6 (honesty):** The README's hook and every benefit line are factually
  true; the per-mode verification status is retained (only text→image is
  "GPU-verified end to end"; all other modes are "implemented · CPU-tested ·
  GPU gate `MIG-S8`"); the full Status & security caveats remain in the README,
  **visible** (never inside a `<details>`), relocated to the end; every "why"
  claim traces to an evidence row.
- **INV-7:** Every internal link in the edited docs resolves to an existing
  file/anchor; the README carries no cloud/Codespaces call to action; the
  reports' typography specifications are treated as non-normative.
- **INV-8:** The Mermaid map reflects the real WebUI → API → generation-container
  flow and is kept small (≤7 nodes) so it reduces rather than adds cognitive
  load; because it is text, it stays maintainable in-repo.

## 4. Gates

- **GATE-LX-S1-TIMEOUT:** `COSMOS3_IDLE_TIMEOUT_SECONDS` defaults to 1800 at
  both sources of truth (`api/app/main.py`, `api/orchestrator/manager.py`); a
  CPU unit test proves the app wires 1800 with no env set, honors an override,
  and treats `0` as disabled; `.env.example` documents the knob consistently;
  the generation/cold-start audit is recorded in `docs/evidence_map.md`; the
  CPU suite (`uv run pytest -m "not gpu"`) is green; no other timeout, schema,
  or route changed; `README.md` untouched.
- **GATE-LX-S2-README:** `README.md` opens with a factually-true hook and a
  copy-paste TL;DR that preserves the runnable quickstart; it contains a
  ≤7-node Mermaid map, collapsible `<details>` for verbose content, sparing
  callouts, and in-page anchors; the full Status & security section is present,
  visible, and at the end, with the five posture facts and the new 30-min idle
  behavior; every "GPU-verified" claim is a subset of the evidence-map verified
  modes (text→image only); every internal link resolves; there is no
  cloud/Codespaces CTA; the WebUI build/lint/typecheck/test are green if any
  non-doc file is touched (none is expected).

## 5. Session Routing

Risk classification follows the requested risk router.

| Session | Risk | Routing | Human gate |
|---|---|---|---|
| LX-S1 Idle keep-warm 600→1800 | low | single agent + deterministic checks + one review | None |
| LX-S2 ADHD README rewrite | low | single agent + deterministic checks + one review, **plus a mandatory adversarial no-over-claim / no-lost-caveat pass** | None (recommended owner read of the rendered README before merge) |

`LX-S1` is low risk: a single constant at two aligned definitions, no schema or
route change, deterministically host-testable, no GPU. `LX-S2` is low risk
(docs-only) but is routed with an explicit adversarial honesty pass because the
owner-chosen punchy-hook direction raises the over-claim hazard (`R-04`); the
phase-3 precedent shows a "low-risk" docs session's full-treatment review is
what caught a real false claim, so the honesty pass is not optional here.

## 6. Change Control

- Do not edit outside a session contract's `blast_radius.allowed_files`.
- Do not change any timeout other than `COSMOS3_IDLE_TIMEOUT_SECONDS`, and do
  not change it anywhere except its two aligned definitions.
- Do not add model weights, generated media, images, or other binaries to the
  repository; the visual map is text (Mermaid).
- Do not add a Codespaces / DevContainer / cloud-development path or CTA.
- Do not split the README into new documents or create a marketing site.
- Treat `README.md` as owned by `LX-S2` only; `LX-S1` must not edit it.
- Do not change public API route shapes or request/response schemas; the idle
  change is a default value only.
- Do not edit `docs/archive/**`.
- Do not change network binding, auth posture, checkpoint revisions, the
  vLLM-Omni pin, or the `MIG-S8` GPU gate.

## 7. Verification Policy

- Classify failures before fixing: BUG, SPEC_GAP, AMBIGUITY, ENVIRONMENT, or
  TEST_BUG (`docs/agent_workflow/prompts/failure_arbiter.md`).
- Prefer deterministic evidence: `uv run pytest -m "not gpu"` for `LX-S1`; for
  `LX-S2`, a relative-link resolver over `README.md`, spec-derived structure /
  honesty asserts (Features "GPU-verified" rows ⊆ evidence-map verified modes;
  Status & security present, visible, at the end; TL;DR / Mermaid / `<details>`
  / anchors present), and `rg` sweeps for a cloud CTA or dropped setup steps.
  If any non-doc file is touched in `LX-S2` (not expected), run the WebUI
  `pnpm build && pnpm lint && pnpm typecheck && pnpm test`.
- No GPU smoke is a blocking gate this phase. GPU inference remains the
  standing `MIG-S8` manual gate, unchanged.
- Claims in user-facing docs must point to an evidence row in
  `docs/evidence_map.md` or be phrased as a limitation (INV-6).

## 8. Done Condition

The phase-4 blueprint's session set is done when `GATE-LX-S1-TIMEOUT` and
`GATE-LX-S2-README` both pass; the `LX-S1` generation/cold-start audit is
recorded in `docs/evidence_map.md`; and `docs/risk_register.md`,
`docs/evidence_map.md`, and `docs/eval_seed_cases.md` reflect the final state of
each session that has closed, including the honesty-pass result for `LX-S2` and
any residual note (e.g. the WebUI SSE-heartbeat consideration, `R-03`/E-08,
left out of scope).
