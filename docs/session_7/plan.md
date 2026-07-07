# Session 7 Plan - README, Project Hygiene, and Beta Polish

Session: MIG-S7
Derived from: `tasks.md` + `design.md`; specs in `specs/*.md`
Convention: TDD where a behavior exists (X-1); document-and-verify for docs/config.
Commit points marked ⎇. Local commits only (no push — that is `MIG-S8`).

## Task 1 — Contract amendment

1. Edit `docs/session_7_contract.yaml`: append to `blast_radius.allowed_files` the entries
   `webui/lib/proxy.ts`, `webui/lib/proxy.test.ts`, `webui/lib/proxyFetch.test.ts`,
   `.gitignore`, `CODE_OF_CONDUCT.md`, `docs/handoff.md`, `docs/eval_corpus/**`,
   `docs/session_7_contract.yaml`. Add an `amendments:` note recording owner approval
   (2026-07-07) and the rationale (X-1 fix + hygiene, mirrors S4 FA-4 / S6 precedent).
2. Verify: `rg -n "proxy.ts|.gitignore|CODE_OF_CONDUCT|handoff|eval_corpus" docs/session_7_contract.yaml`.
   ⎇ `docs(s7): refining pack + contract allowed_files amendment`

## Task 2 — X-1 auth header (TDD)

**2.1 RED — update the assertions to the target header.**
- `webui/lib/proxy.test.ts:38`: `expect(out.get("authorization")).toBe("Bearer secret")`
  → `expect(out.get("x-api-key")).toBe("secret")`; and assert
  `expect(out.get("authorization")).toBeNull()`.
- `webui/lib/proxy.test.ts:43` (the "omits auth" case): assert
  `expect(out.get("x-api-key")).toBeNull()`.
- Add a spoof case to `proxy.test.ts`: incoming `{ "x-api-key": "attacker" }` +
  `filterForwardHeaders(incoming, "server")` → `expect(out.get("x-api-key")).toBe("server")`.
- `webui/lib/proxyFetch.test.ts:47`: `expect(sent.get("authorization")).toBe("Bearer s3cret")`
  → `expect(sent.get("x-api-key")).toBe("s3cret")`.
- Run `cd webui && pnpm test` → the header assertions FAIL against the current `Bearer` code.

**2.2 GREEN — one-line source change.**
- `webui/lib/proxy.ts:37`: `if (apiKey) out.set("authorization", ` + "`Bearer ${apiKey}`" + `);`
  → `if (apiKey) out.set("x-api-key", apiKey);`
- Update the doc comment on the function (lines 28–31) to say it injects the `X-API-Key`
  header the API enforces.

**2.3 Verify.**
```bash
cd webui && pnpm test && pnpm lint && pnpm typecheck
```
All green. ⎇ `fix(s7): WebUI BFF forwards COSMOS3_API_KEY as X-API-Key (X-1)`

## Task 3 — Community-health files

**3.1 `LICENSE`** — MIT text, `Copyright (c) 2026 Feng Wang`. Repo code only.

**3.2 `SECURITY.md`** — sections: Supported Versions (beta / research preview),
Reporting a Vulnerability (GitHub → Security → *Report a vulnerability* private advisory;
email fallback `feng.wang1@hexagon.com`), an explicit "Please do **not** open a public
issue for a security vulnerability", scope note (repo code; model weights and upstream
deps are out of scope / report upstream), and expected response window (best-effort, beta).

**3.3 `CONTRIBUTING.md`** — Getting started (`uv sync`, `pnpm install`), the exact local
check commands mirroring `.github/workflows/ci.yml`:
```bash
# Python (API)
uv run ruff check api tests
uv sync --frozen --group test-cpu && uv run pytest -m "not gpu"
# WebUI
cd webui && pnpm install --frozen-lockfile
pnpm build && pnpm lint && pnpm typecheck && pnpm test
```
GPU tests are a manual gate (`COSMOS3_ENABLE_GPU_TESTS=1 pytest -m gpu`). Commit guidance:
prefer `git add <path>` over `git add .`; conventional-commit style; link
`CODE_OF_CONDUCT.md`; note the blast-radius / contract discipline for `docs/`-driven work.

**3.4 `CODE_OF_CONDUCT.md`** — Contributor Covenant 2.1 verbatim; enforcement contact
`feng.wang1@hexagon.com`.

**3.5 Issue/PR templates:**
- `.github/ISSUE_TEMPLATE/bug_report.yml` — form fields: what happened, repro steps,
  expected, environment (GPU/driver/OS/Docker versions — **not** secrets), checkpoint
  label, logs (with a "redact tokens/paths" note). `labels: [bug, "awaiting triage"]`.
- `.github/ISSUE_TEMPLATE/feature_request.yml` — problem, proposal, alternatives, scope.
  `labels: [enhancement, "awaiting triage"]`.
- `.github/ISSUE_TEMPLATE/config.yml` — `blank_issues_enabled: false`; `contact_links:`
  one entry routing security reports to the `SECURITY.md` policy (not a public issue),
  one to Discussions/README for questions.
- `.github/PULL_REQUEST_TEMPLATE.md` — summary, linked issue, checks run
  (lint/typecheck/tests), contract/blast-radius note, docs updated, no secrets/weights.

**3.6 `docs/release_checklist.md`** — pre-beta GO/NO-GO gate: private-reference scan
clean; license-boundary review (MIT vs `openmdw-1.0`/`other`); README link resolution;
CPU CI green; Docker render + build; **manual GPU gates (`MIG-S8`, `EV-MIG-GPU-*`)**;
hygiene files present; badges/links resolve after publish; tag/release notes. Reference
`docs/evidence_map.md` and `docs/risk_register.md`.

- Verify after 3.x: `uv run python tests/test_private_ref_scan.py` → 0 findings;
  `for f in LICENSE SECURITY.md CONTRIBUTING.md CODE_OF_CONDUCT.md; do test -f "$f"; done`.
  ⎇ `feat(s7): community-health files (LICENSE/SECURITY/CONTRIBUTING/CoC/templates/checklist)`

## Task 4 — `.gitignore` hardening

1. Append to `.gitignore` (keep the existing block):
```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.ruff_cache/
.benchmarks/
# Node / Next
node_modules/
.next/
*.tsbuildinfo
# Build output
dist/
build/
# Model weights & generated media (INV-2) — misc/logo.png stays tracked
models/
*.safetensors
*.pt
*.pth
*.ckpt
*.mp4
*.webm
```
2. Verify no tracked file becomes ignored and the new artifacts are ignored:
```bash
git ls-files | git check-ignore --stdin --no-index --verbose ; echo "exit=$?"   # expect: no tracked path listed (exit 1 = none ignored)
git check-ignore __pycache__/x.pyc .venv/ node_modules/ webui/.next/ models/w.safetensors
git status --short
```
   (`git check-ignore --stdin` prints only ignored inputs; a tracked path appearing is a
   failure. Verify `misc/logo.png` is NOT ignored.)
   ⎇ `chore(s7): harden root .gitignore (build/env/model artifacts)`

## Task 5 — Public README

1. Write `README.md` per `specs/public-readme.md` and `design.md` D-1..D-4/D-7/D-9.
   Structure: logo (centered `misc/logo.png`) → badges → one-liner + subtitle →
   research-preview note → What is this → Features (evidence-qualified matrix) →
   Quickstart → Requirements → Checkpoint setup (license separation + `docs/model_setup.md`
   link) → Development → Limitations & beta status → Troubleshooting → Security / License /
   Contributing / Code of Conduct links.
2. Claim discipline: no literal `production-ready`/`guaranteed`/`always`/`official` token
   used as a claim; use "beta / research preview", "production readiness" (spaced) only in
   negation, "GPU-unverified (`MIG-S8` gate)".
3. Verify:
```bash
test -s README.md
rg -n "production-ready|guaranteed|always|official" README.md    # review each match, expect none as a claim
uv run python tests/test_private_ref_scan.py                     # 0 findings
# link resolution: extract relative link targets and confirm each is tracked
rg -o "\]\(([^)]+)\)" -r '$1' README.md | rg -v '^https?://|^#' | while read -r t; do git ls-files --error-unmatch "$t" >/dev/null || echo "MISSING: $t"; done
```
   ⎇ `docs(s7): public README (evidence-qualified, public-only setup)`

## Task 6 — Verification, review, adversarial

1. Full deterministic checks (see execution_contract). Classify any failure via
   `docs/agent_workflow/prompts/failure_arbiter.md` → `docs/session_7/failure_arbiter.md`.
2. Sharded review over 5 axes (read-only subagents) → `docs/session_7/sharded_review.md`;
   fix High/Critical only; re-run checks.
3. Fresh-context adversarial verifier (contract + diff + evidence only) →
   `docs/session_7/adversarial_verification.md`.
   ⎇ `review(s7): sharded review + fixes` / `docs(s7): adversarial verification`

## Task 7 — Close

1. Update `docs/evidence_map.md` (add the S7 row), `docs/risk_register.md`
   (R-01/R-09/R-11/R-15 mitigated; R-16 partial via X-1; note X-1 closed),
   `docs/eval_seed_cases.md`; add `docs/eval_corpus/mig_s7_*.md`.
2. Verify `GATE-MIG-S7-PUBLIC`; write `docs/handoff.md` (claim matrix, hygiene list, link
   notes, remaining gaps, release-checklist pointer).
   ⎇ `docs(s7): evidence/risk/eval updates + handoff`
