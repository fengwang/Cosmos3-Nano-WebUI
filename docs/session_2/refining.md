# LX-S2 Refining — ADHD-Friendly README Rewrite

Date: 2026-07-24
Session: `LX-S2` · Risk: low · Gate: `GATE-LX-S2-README`
Ceremony: **proportionate** (owner decision, mirrors `LX-S1`). This one file
condenses brainstorming → proposal → design → spec-properties → coarse tasks;
`execution_contract.md` is the executable companion. The session contract
(`docs/session_2_contract.yaml`) and `docs/session_2.md` are already exhaustive,
so this doc extracts the *design*, not a fresh exploration.

Authority: `docs/project_contract.md` → `docs/session_2_contract.yaml` → this
doc. PRD `docs/prd.md` is dominant. On conflict, stop and record it.

---

## 1. Motivation (extracted)

The README is the phase-3 `UX-S4` output: honest and features-first, but a flat
~188-line wall — a top honesty banner front-loading caveats, no visual map, no
progressive disclosure, no in-page navigation (E-09). For the ADHD reader the
three research reports describe (reduced working memory, task-initiation
friction, distractibility), that on-ramp is heavier than it needs to be. The
reports converge on a fix (E-10) and disagree on several points already resolved
by the owner (E-11..E-19). `LX-S1` settled the idle keep-warm at 30 min; this
session is the last phase-4 gate and documents that settled behavior.

The load-bearing hazard is **honesty regression** (`R-04`): a punchier hook with
caveats relocated to the bottom invites over-claiming or a quietly dropped
caveat — the exact false-claim class the phase-3 docs review caught. Honesty is
a hard invariant (INV-6), not a preference, so this low-risk session still
carries a mandatory adversarial no-over-claim / no-lost-caveat pass.

Functional-thinking (ACD) skill: **N/A** — this session's blast radius contains
no code (docs/prose only). Considered and set aside deliberately.

## 2. Approaches considered

- **A1 — Single-file structural ADHD pass (CHOSEN).** Rewrite the one
  `README.md`: punchy true hook → copy-paste TL;DR → ≤7-node Mermaid map →
  `<details>` for verbose content → in-page TOC → tighter chunks; full caveats
  visible at the end; depth linked to existing docs. Matches PRD Decisions 6/7,
  Hard Commitments 5/6/8, and all of In-Scope 1–6. Lowest risk, exactly the
  contract.
- **A2 — Multi-doc split** (README + QUICKSTART + ARCHITECTURE + …). *Rejected*:
  PRD Non-Goal + E-16 (owner chose a single README); adds link surface (more
  `R-08` exposure) and splits the honesty story across files.
- **A3 — Minimal touch** (add a TOC, move the banner, stop). *Rejected*:
  under-delivers — no visual map, no progressive disclosure — and would fail
  `EV-LX-README-STRUCTURE`. The contract asks for the full set of moves.

## 3. Chosen design

### 3.1 Document order (top → bottom)

1. **Header** (kept): centered logo (`misc/logo.png`, existing asset), badge
   row, `# Cosmos3-Nano-WebUI`.
2. **Hook** — a centered, punchy, *factually-true* one/two-liner (value-first):
   what it makes, locally, on your own GPU, from quantized checkpoints, no
   cloud/keys. Replaces the current centered subtitle (merged, no duplication).
   This drops the top honesty banner as its own block.
3. **Honest pointer** — one sparing `> [!NOTE]` (≤2 sentences) directly under
   the hook: trusted-LAN / no-auth / loopback, and *only text→image is
   GPU-verified end to end*, then a link to `#status--security`. This is a
   pointer, **not** the relocated banner — the full five-fact content lives at
   the bottom. It inoculates the punchy hook against over-claim (INV-6, `R-04`)
   the instant a skimmer reads it.
4. **`## Quickstart`** — the copy-paste **TL;DR / fastest path**, near the top.
   Preserves the runnable quickstart verbatim in intent (INV-5): clone → pinned
   public `hf download` → `make build` → `make up-fp8` → `make health` → open
   the Studio. Literal string "TL;DR" appears here (structure assert).
5. **`## What it does`** — short, chunked (≤~4-line paragraphs, one idea each).
6. **`## How it works`** — one ≤7-node Mermaid map (§3.3) + one explanatory line
   that also states the 30-min keep-warm at a glance.
7. **`## Features`** — the capability/endpoint/status **table** kept, with the
   honest per-mode status column intact + the `MIG-S8` footnote.
8. **`## Requirements`** — tightened bullets.
9. **`## Checkpoint setup`** — the checkpoint **table** kept; depth linked to
   `docs/model_setup.md` (not inlined); licensing blockquote kept.
10. **`## Troubleshooting`** — verbose items moved into a collapsible
    `<details>` (blank line after `</summary>`). Essential setup is never here.
11. **`## Status & security`** — the **full** caveats, **visible** (not in
    `<details>`), in the final third. Five posture facts + per-mode verification
    + generation defaults/VRAM + **new**: the 30-min idle keep-warm behavior.
12. **`## Project`** — footer links (sparing purposeful emoji, as today).

A compact in-page nav ("**Jump to:** …") sits right after the Quickstart so the
skimmer gets the fastest path first, then the map of the page.

### 3.2 Honesty rules (INV-6 — hard)

- The hook and every benefit line are literally true; no line implies an
  unverified mode is verified. Per-mode status appears in three places: the top
  honest pointer, the Features status column, and the bottom section.
- Exactly **text→image** is "GPU-verified end to end" (`GPU-S3`). Every other
  mode reads "implemented · CPU-tested · GPU gate (`MIG-S8`)". The 720p t2v
  smoke is described as "passed" but *not* promoted to "verified" (E-20 drift
  guard).
- No caveat is deleted, softened, or hidden in `<details>`. The relocated
  Status & security section is **≥** today's in content (thinner = regression).
- Every "why"/benefit claim traces to an evidence row (`docs/evidence_map.md`)
  or the settled phase-2/3 state.

### 3.3 Mermaid map (≤7 nodes, faithful — INV-8, E-17)

Verified against `deploy/docker-compose.base.yml` + `.fp8.yml` and
`api/orchestrator/*`: browser → Next.js server-side BFF
(`webui/app/api/[...path]/route.ts` → `API_INTERNAL_URL=http://api:8000`) →
FastAPI → Orchestrator (residency + idle keep-warm; drives the container over
the Docker socket) → vLLM-Omni container (`http://vllm-omni:8000`, GPU,
FP8/NVFP4). **5 nodes.** `flowchart LR`, text-only labels (no emoji inside the
diagram, to keep it parseable), no committed image (NFR-1).

### 3.4 Progressive disclosure & navigation

- `<details>`/`<summary>` for **verbose** content only (Troubleshooting; any
  advanced config), never essential setup or caveats (E-13, `R-09`). Blank line
  after every `</summary>` (broken-render guard, `R-09`).
- Headings kept **emoji-free** so GitHub anchor slugs stay predictable (nav is
  an ADHD principle; fragile anchors are `R-08`). Sparing emoji only in the
  non-anchor `## Project` footer bullets (as today).
- `## Status & security` keeps that exact name → stable anchor `#status--security`
  (already used by in-page links today).
- Callouts kept **sparing**: one `> [!NOTE]` (honest pointer). Licensing stays a
  plain blockquote. "If everything is emphasized, nothing is."

### 3.5 Explicitly not adopted (report-vs-reality)

No Codespaces / DevContainer / "run in the cloud" CTA anywhere (E-12, `R-06`) —
local RTX 5090 required. Typography specs treated as non-normative — GitHub
controls README rendering (E-14, INV-7). No bionic reading (E-15). Single file,
no split, no site (E-16).

## 4. Spec-derived testable properties → checks

| # | Property (from contract) | Verified by |
|---|---|---|
| P1 | Runnable TL;DR: clone → pinned `hf download` → `make build` → `make up-fp8` → `make health` → Studio, each `make` target in `Makefile`, in fenced block | `EV-LX-README-RUNNABLE-QUICKSTART` |
| P2 | Full Status & security **visible** (not in `<details>`), in final third, five posture facts + 30-min idle behavior | `EV-LX-README-HONEST-CAVEATS` |
| P3 | Only text→image claimed GPU-verified; every other mode CPU-tested + `MIG-S8`; no benefit line implies otherwise | `EV-LX-README-VERIFIED-SUBSET` |
| P4 | Hook precedes deep install; "TL;DR" near top; ≥1 `mermaid` fence (≤7 nodes); ≥1 `<details>`/`<summary>` (blank line after `</summary>`); in-page anchors/TOC | `EV-LX-README-STRUCTURE` |
| P5 | Every relative link + in-page anchor resolves; zero codespace/devcontainer/cloud CTA | `EV-LX-DOCS-LINKS-RESOLVE` |
| P6 | Single file; depth linked to `CONTRIBUTING.md` / `docs/model_setup.md`, not inlined | review (FR-10) |

## 5. Coarse task list (dependency order)

1. **T1 — Rewrite `README.md`** to the §3 design (hook + honest pointer +
   Quickstart/TL;DR + What it does + How-it-works Mermaid + Features + Reqs +
   Checkpoint setup + Troubleshooting `<details>` + full visible Status &
   security incl. 30-min idle + Project footer + TOC).
2. **T2 — Deterministic checks** (P1–P5): build a repeatable link/anchor
   resolver + structure/honesty/CTA sweeps over `README.md`; cross-check `make`
   targets against `Makefile`.
3. **T3 — Sharded review** (6 axes) — read-only, dedup, fix only High/Critical.
4. **T4 — Adversarial honesty pass** — fresh-context, tries to falsify the done
   condition (over-claim / lost caveat / broken `<details>` / dropped step /
   cloud CTA / dangling anchor / oversized map).
5. **T5 — Close-out** — update `docs/evidence_map.md` (LX-S2 harvest),
   `docs/risk_register.md` (R-04/06/08/09/10 → Closed), `docs/eval_seed_cases.md`
   (LX-S2 results), `docs/handoff.md`; note the residual SSE heartbeat
   (E-08/R-03) as a future consideration. Commit at clean checkpoints.

## 6. Out of scope (guardrail)

Any code/config/WebUI change (the timeout is `LX-S1`); splitting the README or
building a site; a Codespaces/DevContainer/remote-dev path; committing any
image/GIF/binary; rewriting `CONTRIBUTING.md` / `SECURITY.md` /
`docs/model_setup.md` substance (link-correctness only); editing
`docs/archive/**`.
