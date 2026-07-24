# PRD - Single-GPU Comfort and ADHD-Friendly Onboarding

Date: 2026-07-24
Status: Draft blueprint (revised after adversarial review), documentation first
Owner: Feng
Related: `docs/project_contract.md`, `docs/evidence_map.md`,
`docs/risk_register.md`, `docs/eval_seed_cases.md`,
`docs/session_{1,2}.md`, `docs/session_{1,2}_contract.yaml`. Prior phases are
archived under `docs/archive/phase-1/` (migration, `MIG-S*`),
`docs/archive/phase-2/` (GPU release readiness, `GPU-S*`), and
`docs/archive/phase-3/` (UX simplification / trusted-LAN posture, `UX-S*`);
they are prior-art input to this blueprint and are not edited by this phase.
The ADHD research reports under `docs/adhd/` are the deep-study input to the
README session (cited per row in `docs/evidence_map.md`).

## 1. Problem

Cosmos3-Nano-WebUI is deployed the way phase-3 settled it: a single
RTX 5090-class machine on a trusted LAN, driven by one user or a small team,
with good output as the zero-configuration default (`docs/archive/phase-3/`).
Two rough edges remain for the "clone it, run a few commands, click a few
times" first-run experience this project targets:

- **The model gets evicted during think-time.** After a generation job
  finishes, the orchestrator starts an idle timer and evicts the resident
  generation plane (a process-group kill that frees VRAM) if no new job
  arrives within `COSMOS3_IDLE_TIMEOUT_SECONDS`, which defaults to **600 s
  (10 min)** (`api/app/main.py:173`; eviction in `api/orchestrator/manager.py`
  `notify_idle`/`_on_idle_timeout`/`_try_idle_evict`). A user who generates a
  clip, watches it, thinks, and tweaks the prompt more than ten minutes later
  pays a full cold start again (model reload inside the freshly restarted
  container). On a single 5090 that iteration loop is the normal way of
  working, so the default punishes exactly the intended use.

- **The README is honest and features-first but not built for fast
  orientation.** The current README is the phase-3 `UX-S4` output: it leads
  with features and a runnable quickstart and keeps a slim honest Status &
  security section (`README.md`). But it is a flat ~188-line wall with no
  visual map of how the pieces fit, no progressive disclosure for verbose
  setup, no in-page navigation, and an honesty note at the very top that
  front-loads caveats before the reader sees what the project can do. For a
  reader who skims, loses their place, and abandons on friction — the ADHD
  reader the research reports describe — the on-ramp is heavier than it needs
  to be.

Neither is a defect. The eviction timing is a resource-hygiene default tuned
for a cautious shared box; the README is honest but structurally dense. Both
are posture mismatches for a single-user 5090 appliance whose first job is to
get someone from "just cloned this" to "watching my first generation" without
friction.

### 1.1 Framing correction (adversarial pass)

The originating request was "increase the default timeout from 10 min to
30 min, to make a 5090 GPU work with default settings," described as the
**video-generation** timeout. Direct source inspection shows the only 10-min
(600 s) default in the tracked tree is the **idle keep-warm** timeout above; it
does **not** bound how long a generation may run. The generation-duration
timeouts already exceed 30 min — `COSMOS3_GEN_TIMEOUT` defaults to 2400 s
(40 min) on the IPC path (`api/jobs/gen_client.py:129`) and 7200 s (2 h) on the
vLLM-Omni HTTP path (`api/engines/vllm_omni/work.py:41,128`) — and the
cold-start readiness ceiling is already 30 min (`COSMOS3_PLANE_READY_TIMEOUT`
= 1800 s, `api/app/main.py:177`, matching the container's `--init-timeout 1800`
in `deploy/vllm-omni.Dockerfile:41`). This blueprint therefore raises the
**idle keep-warm** timeout (the knob that actually causes the "cold reload
after I pause" pain), and treats "confirm the generation and cold-start
ceilings already cover ≥30-min work" as an audit, not a change
(`docs/evidence_map.md` E-01..E-04).

## 2. Goal

Make a single RTX 5090 comfortable to run with default settings, and make the
README fast to orient in for a reader who skims — without loosening the
project's honest posture.

Concretely: raise the idle keep-warm default so the resident model survives a
normal think-and-iterate loop (30 min instead of 10) and document that
generation and cold-start ceilings already accommodate long jobs; and rewrite
the README as an ADHD-friendly on-ramp (a punchy but truthful hook, a
copy-paste TL;DR, a small visual map, progressive disclosure for verbose
detail, in-page navigation) that keeps every current fact and relocates — but
never deletes or hides — the honest Status & security caveats.

This is a documentation-and-blueprint pass only. It defines the sessions,
contracts, and gates that later development sessions execute one at a time; it
does not itself change application code, configuration, or the README beyond
the blueprint documents in `docs/`.

## 3. Owner Decisions

These decisions are binding for this blueprint and the sessions it defines.
They were fixed with the owner during the interview that produced this
blueprint (2026-07-24).

1. **Phase identity.** Session IDs are `LX-S1` and `LX-S2` (phase-4,
   "Local-5090 eXperience"). Deliverables are written at `docs/` root (prior
   phases are archived); numbering is fresh 1..2. Gates are
   `GATE-LX-S1-TIMEOUT` and `GATE-LX-S2-README`.
2. **Timeout target and value.** The change is to the **idle keep-warm**
   timeout only: `COSMOS3_IDLE_TIMEOUT_SECONDS` default **600 → 1800** (10 →
   30 min). The "video-generation timeout" framing is corrected in the
   evidence map; the generation and cold-start ceilings are audited (already
   ≥30 min) and left unchanged.
3. **Timeout is a default, not a lock.** The value stays operator-configurable
   via the existing environment variable; the blueprint only changes the
   shipped default and surfaces the knob. `0` remains "disabled" (never evict)
   per the existing `notify_idle` contract.
4. **"Default settings" means the code default.** `COSMOS3_IDLE_TIMEOUT_SECONDS`
   is not currently in `.env.example`; `LX-S1` changes the code default so no
   `.env` edit is required, and additionally surfaces the variable in
   `.env.example` (commented) for discoverability.
5. **Two sessions, timeout first.** `LX-S1` (timeout) runs before `LX-S2`
   (README) so the README documents the settled 30-min default. `LX-S1` does
   **not** edit `README.md`; `LX-S2` owns all README prose (avoids the
   shared-surface conflict phase-3 tracked as its `R-09`).
6. **README: structural ADHD pass on a single file.** One `README.md` (not a
   split into multiple docs). Adopt: a punchy hook, a copy-paste TL;DR /
   fastest-path, a small Mermaid "how it works" map, collapsible `<details>`
   for verbose/advanced/troubleshooting content, sparing GFM callouts,
   in-page TOC/anchors, and tighter chunking. Depth continues to live in the
   existing `CONTRIBUTING.md` / `docs/model_setup.md` (linked, not inlined).
7. **Punchy hook, honest caveats at the bottom — visible, never hidden.** The
   hook leads and the current top honesty banner is dropped, but the **full**
   Status & security content stays in the README, visible (not inside a
   collapsible), relocated to the end. The hook MUST be factually true; the
   per-mode verification status MUST remain (only text→image is GPU-verified
   end to end); no "why" claim may outrun an evidence row.
8. **Resolve report-vs-reality conflicts explicitly.** Drop the reports'
   GitHub Codespaces / DevContainer "zero-friction remote development"
   recommendation (a local RTX 5090 is required; Codespaces provide no
   suitable GPU), and treat the reports' README-typography advice
   (font/line-height/alignment) as non-normative (GitHub controls README
   rendering). Each disagreement is stated in `docs/evidence_map.md` with the
   chosen path.
9. **Verification posture.** Both sessions are verifiable with deterministic,
   host-run checks; **no GPU smoke is required** this phase. Idle eviction is
   host-testable via the orchestrator's injected timer; the README session is
   verified by link/structure/honesty checks. GPU inference remains the
   standing `MIG-S8` manual gate, untouched here.

## 4. Requirements

Requirement keywords follow RFC 2119. A claim not yet verified at blueprint
time is written as a verification task or session gate, not a shipped
capability.

### Functional

- **FR-1 (MUST)** `LX-S1` changes the shipped default of
  `COSMOS3_IDLE_TIMEOUT_SECONDS` from `600` to `1800` at its source of truth
  in `api/app/main.py:173`, and aligns the `Orchestrator` constructor default
  (`api/orchestrator/manager.py` `idle_timeout=600.0 → 1800.0`) so a
  directly-constructed orchestrator cannot silently drift from the wired
  default (`docs/evidence_map.md` E-06).
- **FR-2 (MUST)** After `LX-S1`, the app built with no timeout environment
  variables set wires an idle keep-warm of 1800 s; an explicit
  `COSMOS3_IDLE_TIMEOUT_SECONDS` override is still honored; `0` still disables
  eviction. Proven by a CPU unit test, not by inspection alone.
- **FR-3 (MUST)** `LX-S1` surfaces `COSMOS3_IDLE_TIMEOUT_SECONDS` in
  `.env.example` with a one-line comment stating it is the idle keep-warm
  window in seconds (default 1800 = 30 min, `0` = never evict), consistent
  with the code default.
- **FR-4 (MUST)** `LX-S1` records an audit in `docs/evidence_map.md` showing
  the generation-duration timeouts (`COSMOS3_GEN_TIMEOUT` 2400 s / 7200 s) and
  the cold-start ceiling (`COSMOS3_PLANE_READY_TIMEOUT` 1800 s) already meet or
  exceed 30 min, so the idle change is the one that serves the goal. It does
  **not** change those values.
- **FR-5 (MUST)** `LX-S1` changes no public API request/response schema shape,
  no route behavior, and no other timeout; the only behavioral change is that
  an idle resident plane is evicted after 30 min instead of 10.
- **FR-6 (MUST)** `LX-S2` rewrites `README.md` into an ADHD-friendly on-ramp:
  a factually-true hook; a copy-paste TL;DR that preserves the runnable
  quickstart (clone → download a pinned public checkpoint → `make build` →
  `make up-fp8` → `make health` → open the Studio); a small (≤7-node) Mermaid
  map of the WebUI → API → generation-container flow; collapsible `<details>`
  for verbose/advanced/troubleshooting content; sparing GFM callouts; and
  in-page anchors/TOC.
- **FR-7 (MUST)** After `LX-S2`, the README's **full** Status & security
  content is present and **visible** (not inside a `<details>`), relocated to
  the end of the document. It states the five posture facts (no application
  auth; loopback default with LAN as an explicit opt-in; root-equivalent
  Docker socket; guardrails-off; honest per-mode verification) and reflects
  the new 30-min idle keep-warm behavior.
- **FR-8 (MUST)** After `LX-S2`, every "GPU-verified" claim in the README is a
  subset of the modes verified in `docs/evidence_map.md` / the archived
  phase-2/phase-3 evidence — i.e. only text→image (`GPU-S3`) is called
  "GPU-verified end to end"; every other mode is "implemented · CPU-tested ·
  GPU gate (`MIG-S8`)". No hook or benefit line implies an unverified mode is
  verified.
- **FR-9 (MUST)** After `LX-S2`, every internal link in `README.md` (and any
  doc it links that the session edits) resolves to a file/anchor that exists;
  the README contains no "launch in the cloud / Codespaces" call to action.
- **FR-10 (SHOULD)** `LX-S2` keeps the README a single file with depth linked
  out to the existing `CONTRIBUTING.md` and `docs/model_setup.md` rather than
  inlined, and keeps the rendered length lean via progressive disclosure.

### Non-Functional

- **NFR-1 (MUST)** No secret, token, private host, private absolute path,
  model weight, or generated-media binary is committed to this repository as
  part of this work. The Mermaid map is text (no committed image); any demo
  image reuses an existing repository asset.
- **NFR-2 (MUST)** Every release-affecting recommendation in
  `docs/project_contract.md` has an evidence row in `docs/evidence_map.md` or
  is marked speculative / owner-decision with a named verification gate.
  Speculative claims do not become MUST requirements.
- **NFR-3 (MUST)** Where the three ADHD reports disagree, the disagreement is
  stated in `docs/evidence_map.md` and one path is chosen; report
  recommendations that contradict repository reality (local-GPU requirement)
  or the GitHub-Markdown rendering model are recorded as not adopted, with the
  reason.
- **NFR-4 (MUST)** Each session's blocking exit criteria are deterministic and
  host-runnable (CPU unit test, `rg`/link/structure sweeps); no GPU smoke is a
  blocking gate this phase.
- **NFR-5 (MUST)** The README rewrite preserves reproducibility from public
  inputs: the pinned public checkpoint download and the `make` targets in the
  quickstart remain accurate against the `Makefile` and `docs/model_setup.md`.

## 5. Acceptance Criteria

This blueprint's scope is done only when all are true:

1. `docs/prd.md`, `docs/project_contract.md`, `docs/evidence_map.md`,
   `docs/risk_register.md`, and `docs/eval_seed_cases.md` exist at `docs/`
   root, and `docs/session_{1,2}.md` / `docs/session_{1,2}_contract.yaml`
   exist for `LX-S1` and `LX-S2`.
2. Each session document defines objective, in-scope, out-of-scope,
   deliverables, and exit criteria, and references the repository evidence and
   (for `LX-S2`) the ADHD reports it depends on.
3. Each session contract classifies risk, routes per the risk router, and
   fixes a blast radius (allowed/forbidden files), invariants, deterministic
   checks, adversarial cases, and a done condition.
4. `docs/evidence_map.md` carries a row for every major recommendation, marks
   speculative/owner-decision claims (never promoting them to MUST), and states
   each cross-report disagreement with the chosen path.
5. The contract pack survives a second, adversarial compilation pass: the
   wrong-timeout framing, the idle-default drift, the README honesty-regression
   hazard, the S1/S2 shared-surface overlap, and the Codespaces / typography
   report-vs-reality conflicts are each resolved in the text rather than left
   latent.
6. No application code, configuration, or non-`docs/` content is modified by
   this pass.

## 6. Non-Goals

- Writing or editing any application code, configuration, `README.md`, or
  non-`docs/` content during this blueprint pass. This PRD and its companions
  define sessions; they do not execute them.
- Changing the generation-duration timeouts (`COSMOS3_GEN_TIMEOUT`), the
  cold-start ceiling (`COSMOS3_PLANE_READY_TIMEOUT`), the reasoner timeout, or
  the WebUI SSE heartbeat. Only the idle keep-warm default changes; the rest
  are audited and left as-is (`docs/evidence_map.md` E-03/E-04/E-08).
- Adding a GitHub Codespaces / DevContainer / remote-development path, or any
  "run it in the cloud" onboarding — the project requires a local RTX 5090.
- Splitting the README into multiple new documents, or building a
  landing/marketing site; the ADHD pass is structural on the single existing
  `README.md`, with depth linked to existing docs.
- Any GPU smoke, GPU validation of any mode, or change to the standing
  `MIG-S8` manual gate.
- Changing checkpoint revisions, the vLLM-Omni pin, network binding, auth
  posture, or anything in `docs/archive/**`.

## 7. Session Plan

| # | Session | Risk | Primary gate |
|---|---|---|---|
| 1 | Extend idle keep-warm to 30 min: `COSMOS3_IDLE_TIMEOUT_SECONDS` 600→1800 (`main.py` default + `manager.py` default + `.env.example` + unit test), audit gen/ready ceilings | low | `GATE-LX-S1-TIMEOUT` |
| 2 | ADHD-friendly README rewrite: punchy true hook + TL;DR + Mermaid map + collapsibles + TOC, full honest caveats visible at the bottom | low | `GATE-LX-S2-README` |
