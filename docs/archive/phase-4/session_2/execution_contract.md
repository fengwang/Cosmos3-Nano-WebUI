# LX-S2 Execution Contract

Date: 2026-07-24
Session: `LX-S2` — ADHD-friendly README rewrite. Gate: `GATE-LX-S2-README`.
Companion to `docs/session_2/refining.md`. Bounded by
`docs/session_2_contract.yaml` and `docs/project_contract.md`.

## Planned file changes

| File | Change | Authority |
|---|---|---|
| `README.md` | Full rewrite to the refining §3 design | FR-6/7/8/9/10, In-Scope 1–6 |
| `docs/session_2/refining.md` | Refining pack (done) | proportionate ceremony |
| `docs/session_2/execution_contract.md` | This file | Execution Contract step |
| `docs/session_2/sharded_review.md` | Review output | Review Phase |
| `docs/session_2/adversarial_verification.md` | Adversarial pass output | Adversarial Verification |
| `docs/evidence_map.md` | LX-S2 execution harvest rows | Handoff |
| `docs/risk_register.md` | R-04/06/08/09/10 → Closed w/ evidence | Handoff |
| `docs/eval_seed_cases.md` | LX-S2 deterministic-check results | Session End |
| `docs/handoff.md` | Rewrite for the closed LX-S1+LX-S2 phase | Session End |

`docs/session_2/failure_arbiter.md` only if a check fails and needs
classification (created on demand).

## Allowed blast radius (hard)

- **Allowed:** `README.md`, `docs/session_2/**`, `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/handoff.md`.
- **Forbidden:** any `api/**`, `webui/**`, `deploy/**`, `schemas/**`, `tests/**`;
  `.env`, `.env.example`; `api/app/main.py`, `api/orchestrator/manager.py`;
  `CONTRIBUTING.md`, `SECURITY.md`, `docs/model_setup.md` (link-correctness only,
  and only if forced — otherwise untouched); `docs/archive/**`; any
  image/GIF/weight/media binary.
- The verification harness lives in the session **scratchpad**, never committed
  to the repo (keeps stray files out of the tree; S2 cannot add a `tests/` file).

## First check to write (TDD-style, before the rewrite)

A single deterministic checker (`check_readme.py`, run under `uv run python`
from the scratchpad) asserting P1–P5 from `refining.md §4`:

1. **Links/anchors (P5):** every `[..](target)` in `README.md` — relative file
   paths exist; in-page `#anchor`s match a GitHub-slugified heading in the file.
2. **CTA sweep (P5):** `codespace|devcontainer|open in cloud|launch in the cloud`
   → 0 matches.
3. **Quickstart (P1):** the six steps present and ordered inside a ```bash fence;
   `make build|up-fp8|health` each grep-confirmed to exist in `Makefile`.
4. **Structure (P4):** a `TL;DR` string in the top third; ≥1 ```mermaid fence
   with ≤7 nodes; ≥1 `<details>` each with `<summary>` and a blank line after
   `</summary>`; a TOC / ≥3 in-page anchor links.
5. **Honesty (P2/P3):** a `## Status & security` heading, **not** inside
   `<details>`, positioned in the final third; the five posture-fact keywords
   present (auth, loopback/`BIND_ADDR`, docker socket, guardrails, per-mode
   verification) + a 30-min / 1800 idle keep-warm statement; every
   "GPU-verified … end to end" line mentions only text→image / t2i.

Run it on the **current** README first (expect: structure + honesty-placement
asserts FAIL — no mermaid/`<details>`/TL;DR, banner on top) to prove the checker
bites; then rewrite until green.

## Checks to run after each task

- **After T1 (rewrite):** `uv run python check_readme.py` → all P1–P5 green;
  plus manual read for chunking/tone. Classify any failure with the Failure
  Arbiter before touching the README again.
- **No code touched** ⇒ no `pytest`/`pnpm` gate required (project contract §7).
  If any non-doc file is somehow touched (not expected), run the WebUI
  `pnpm build && pnpm lint && pnpm typecheck && pnpm test`. Guard with
  `git diff --name-only` staying within the allowed set.

## Review axes to run at the end (T3)

Sharded, read-only, per `docs/agent_workflow/prompts/sharded_review.md`:
correctness, readability/simplicity, security/safety, tests, architecture,
performance. For a docs diff the load-bearing axes are **correctness (honesty /
factual accuracy / link integrity)**, **readability**, and **security (no leaked
private path/secret; caveats intact)**. Dedup; fix only High/Critical (or
strong-evidence Medium), then re-check.

## Adversarial verifier brief (T4)

Fresh context; sees only the session + project contracts, the `git diff`, and
the check evidence — **not** this conversation. Job: falsify
`GATE-LX-S2-README`. Must probe every `adversarial_case` in the contract:
over-claiming hook; dropped/softened/hidden caveat; cloud/Codespaces CTA;
dropped/reordered setup step; broken `<details>` or essential-content-only-in-
`<details>`; unsupported "why" claim; oversized/misleading Mermaid map; dangling
link/anchor after restructure; per-mode wording drifting ahead of the evidence
map. Output: disproven claims, unsupported claims, strongest counterexample,
PASS/FAIL. A FAIL is classified with the Failure Arbiter before any fix.

## Concrete done condition

`GATE-LX-S2-README` passes: `README.md` opens with a factually-true hook + a
runnable copy-paste TL;DR (every `make` target in `Makefile`); contains a
≤7-node Mermaid map, `<details>` for verbose content, and in-page navigation;
the **full** Status & security section is present, **visible** (not collapsed),
in the final third, with the five posture facts and the 30-min idle keep-warm
behavior; only text→image is claimed GPU-verified; every internal link/anchor
resolves; no cloud CTA; the README stays a single file with depth linked out —
**and** the adversarial honesty pass records no surviving over-claim or
lost/hidden caveat. Deterministic checker green with recorded output;
sharded review with no open High/Critical; close-out docs updated; work
committed at clean checkpoints on `fea/doc-adhd-optimization` (no PR).
