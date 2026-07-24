# UX-S4 Plan — README / Docs Friendliness (executable, TDD-style)

Source: `docs/session_4/tasks.md`, `specs/*.md`, `design.md`.
"Test-first" for a docs session = write the deterministic check first, watch it
fail on the current tree (red), edit, watch it pass (green).

## Conventions

- Repo root: `/workspace/github.repo/Cosmos3-Nano-WebUI`.
- Checker script (session-local, not committed to the app):
  `scratchpad/check_docs.py` — link resolver + spec-derived greps.
- Commit points marked ⎇; commit only at clean checkpoints.

## Step 1 — Verification harness (RED baseline)

1. Write `check_docs.py`: for each of `README.md`, `SECURITY.md`,
   `CONTRIBUTING.md`, extract `[..](target)` links + `<img src=...>` + HTML
   `href=`; skip `http(s)://`, `mailto:`, and pure `#anchor`; strip `#frag`;
   resolve the rest against repo root; print `UNRESOLVED <file>:<link>` for any
   miss. Also run the two sweeps.
2. Run it. **Expect RED:** `README.md` → `docs/release_checklist.md` resolves
   *today* (file still exists) but is the archived-artifact link to be dropped;
   `rg "release_checklist|R-16"` → 2 hits (README:202, SECURITY:55). Record.

```bash
uv run python scratchpad/check_docs.py
rg -n "release_checklist|R-16" README.md SECURITY.md
rg -n "COSMOS3_API_KEY|X-API-Key" README.md SECURITY.md   # expect: already clean
```

## Step 2 — CONTRIBUTING owns dev/CI (Task 2.1)

1. Edit `CONTRIBUTING.md`: add `uv python install 3.12` to Development setup;
   add "these mirror the CPU-only CI in `.github/workflows/ci.yml`" framing where
   the checks are introduced; reword the "and the release checklist" prose (line
   ~52) to reference `docs/risk_register.md` (R-05) + `docs/evidence_map.md`
   only (no archived release-checklist implication).
2. Confirm: `rg -n "uv sync|pnpm build|ruff|pytest" CONTRIBUTING.md` shows the
   full workflow present.
⎇ (defer commit; bundle with README so the move is atomic).

## Step 3 — README restructure (Task 3.1–3.7)

Rewrite `README.md` per `design.md` D1. Key literal facts to preserve exactly:

- Clone: `git clone https://github.com/fengwang/Cosmos3-Nano-WebUI.git`
- Download (pinned FP8):
  `hf download wfen/Cosmos3-Nano-FP8-Blockwise --revision
  9bf5d6ae164688487bdb71947ccc6ebe70d12900 --local-dir
  ./models/Cosmos3-Nano-FP8-Blockwise`
- `make build` → `make up-fp8` → `make health` → `http://localhost:3000`
- Checkpoint table: FP8 `9bf5d6ae1646…` `openmdw-1.0`; NVFP4 `5514c42b9759…`
  `openmdw-1.0`; BF16 base `nvidia/Cosmos3-Nano` `fea6e03a…` `other`.
- Links to keep (all verified to resolve): `LICENSE`, `SECURITY.md`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `docs/model_setup.md`,
  `docs/evidence_map.md`, `docs/risk_register.md`, `misc/logo.png`,
  `.github/workflows/ci.yml`.
- **Remove:** the "Development" command block; the "Release readiness →
  `docs/release_checklist.md`" bullet; the top `[!WARNING]` framing.

Then GREEN-check: `uv run python scratchpad/check_docs.py` → no UNRESOLVED;
`rg "release_checklist" README.md` → none; and the spec-derived asserts
(features before quickstart; each quickstart essential present; no dev command
block in README).

## Step 4 — SECURITY.md + layout.tsx (Task 4.1–4.2)

1. `SECURITY.md`: change `See docs/risk_register.md (R-16).` → point at the live
   `R-01` (socket-after-auth-removal, carries R-16 forward); add one line: the
   generation stack ships with guardrails off by default (unfiltered output;
   required for the 720p default to fit — trusted-LAN posture).
2. `webui/app/layout.tsx`: `description` → subtitle mirror; `{/* … used from S9. */}`
   → generic. Copy-only.

GREEN-check: `rg -n "R-16" README.md SECURITY.md` → none; then from `webui/`:

```bash
cd webui && pnpm build && pnpm lint && pnpm typecheck && pnpm test
```

⎇ Commit the doc restructure + layout copy fix once all deterministic checks are
green: `docs(ux-s4): features-first README + CONTRIBUTING dev/CI + honest callout`.

## Step 5 — Full deterministic checks (Task 5)

Re-run the resolver + both sweeps + spec asserts; confirm `webui` suite green.
Classify any failure (BUG/SPEC_GAP/AMBIGUITY/ENVIRONMENT/TEST_BUG) before fixing.

## Step 6 — Review + adversarial (Task 6)

- 6-axis sharded review (read-only), dedupe, fix only High/Critical, re-check →
  `docs/session_4/sharded_review.md`.
- Fresh-context adversarial verifier vs `GATE-UX-S4-DOCS` →
  `docs/session_4/adversarial_verification.md`.
⎇ Commit review + evidence.

## Step 7 — Close-out (Task 7)

Update `evidence_map.md` / `risk_register.md` (R-08, R-09 resolved) /
`eval_seed_cases.md` (`EV-UX-DOCS-LINKS-RESOLVE`); write `docs/handoff.md`; add
`docs/eval_corpus/ux-s4-docs-friendliness.md`.
⎇ Commit `docs(ux-s4): close session — evidence/risk/handoff/eval`.
