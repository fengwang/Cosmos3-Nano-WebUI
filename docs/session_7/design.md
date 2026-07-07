# Session 7 Design - README, Project Hygiene, and Beta Polish

Session: MIG-S7
Risk: medium · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S7-PUBLIC`
Derived from: `proposal.md` (capabilities) + `brainstorming.md` (approved design)

## Context

`MIG-S1`..`MIG-S6` produced a curated public repo with runtime source, verified public
checkpoints, CPU-only CI, and local-build Docker/Compose — but no public README and no
community-health files. Everything runtime is GPU-unverified (the `MIG-S8` gate). Stakeholders
are (a) GitHub visitors deciding whether to engage, (b) operators cloning and running from
public inputs, and (c) contributors filing issues/PRs. Constraints: public-verifiable evidence
only, three-way license separation (`INV-7`), no private paths/hosts (`INV-1`), no new
dependency (`INV-10`), and a tight blast radius (docs + hygiene files) — extended this session,
with owner approval, to the X-1 client fix and `.gitignore`.

## Goals / Non-Goals

**Goals**
- A concise, honest, public-only README that a stranger can follow from clone to a running
  local stack, with every runtime claim evidence-qualified.
- The community-health file set, safe by construction (private security reporting; no
  sensitive-data fields; license boundaries explicit).
- Fix X-1 so `COSMOS3_API_KEY` actually authenticates the WebUI→API path.
- A `.gitignore` fit for an open contribution repo.

**Non-Goals**
- No new runtime feature; no Docker publishing; no GPU CI; no production-readiness claim.
- No change to the public API surface (routes, methods, request/response shapes).
- No editing of model cards outside this repo; no push/release (that is `MIG-S8`).

## Decisions

- **D-1 — Concise README that links to `docs/model_setup.md` (not a duplicate).** The
  authoritative checkpoint facts already live in a tracked public doc; duplicating them would
  rot. *Alternative:* inline everything (rejected — violates "keep concise", risks the
  "hides setup steps" failure mode). Ref: brainstorming A1.
- **D-2 — Evidence-qualified feature matrix keyed to verification state.** Each mode is
  labelled *code present · GPU-unverified (S8 gate)*, citing the evidence map / `model_setup.md`.
  No performance numbers, no "supports RTX 5090" as a bare claim. Ref: `INV-6`/`INV-8`, R-09.
- **D-3 — Quickstart is local-build + public-download only.** `git clone` →
  `huggingface-cli download <public repo> --revision <pin>` → `make build` → `make up-fp8`.
  No registry image, no private path, no absolute host path (examples use `/path/to/...` or
  repo-relative `./models/<Repo>`). Ref: `INV-1`/`INV-3`/adversarial case 3.
- **D-4 — Three-way license separation, stated wherever weights appear.** Repo code = **MIT**
  (`LICENSE`); FP8/NVFP4 weights = **`openmdw-1.0`**; base `nvidia/Cosmos3-Nano` = **`other`**.
  The README's license section and the checkpoint-setup section both say the MIT license does
  **not** cover the model weights. Ref: `INV-7`, R-11, adversarial case 2.
- **D-5 — X-1 fixed on the client, toward the API's contract header.** Change
  `webui/lib/proxy.ts` to `out.set("x-api-key", apiKey)`. The API's `X-API-Key` contract is
  unchanged (`INV-9`); `Headers.set()` overwrites any client-supplied value (no spoofing).
  *Alternative:* broaden `api/app/auth.py` to accept `Bearer` (rejected — widens server auth
  surface, edits contract code). Ref: proposal §3, R-16.
- **D-6 — `SECURITY.md` routes to a private channel and forbids public issues.** Use GitHub
  private vulnerability reporting (Security tab) with an email fallback; state the supported
  surface is beta/research-preview and coordinated-disclosure only. `config.yml` sets
  `blank_issues_enabled: false` and adds a contact link that redirects security reports away
  from public issues. Ref: adversarial case 4, R-15, failure mode "issue templates request
  sensitive data".
- **D-7 — CI badge included but flagged as at-publish.** The GitHub Actions status badge
  (`.github/workflows/ci.yml/badge.svg`) is standard and honest; it renders once the repo is
  public. Static shields.io badges (License/Python/Status) carry no rot risk. Ref: owner
  decision 3, failure mode "links rot before beta".
- **D-8 — `.gitignore` adds standard excludes without dropping tracked files.** Append
  `__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`, `node_modules/`, `.next/`, `.ruff_cache/`,
  `.pytest_cache/`, `.benchmarks/`, `dist/`, `build/`, `*.tsbuildinfo`, `models/`, and media
  globs. Verified with `git ls-files` + `git check-ignore` that no tracked path becomes
  ignored. Ref: proposal §4, `INV-2`.
- **D-9 — README length budget.** Target a scannable single screen of intro + a body that
  moves detail to `docs/`. The final review checklist (no broken links, no empty sections,
  consistent naming) is applied before close. Ref: `references/readme.howto.md`.

## Risks / Trade-offs

- **[Overclaiming GPU/perf (R-09)]** → every runtime line is evidence-qualified; adversarial
  verifier specifically tries to find a bare "shipped GPU support" claim.
- **[License conflation (R-11)]** → three-way separation stated in two places; adversarial
  case 2 tested.
- **[Self-referential link/badge rot]** → only the CI badge and repo-relative doc links can
  break pre-publish; documented as an at-publish checklist item; all doc links target tracked
  files (verified with `git ls-files`).
- **[X-1 fix touches product code (out of original radius)]** → owner-approved amendment;
  smallest possible change (one line + tests); `INV-9` preserved; full WebUI test/lint/typecheck
  run; the change is covered by both `proxy.test.ts` and `proxyFetch.test.ts`.
- **[`.gitignore` accidentally ignores a tracked file]** → `git check-ignore` over the tracked
  set as a gate; `git status` stays clean after the edit.
- **[Forbidden-claims scan false positives on the whole tree]** → interpreted as a heuristic;
  enforced over S7 deliverables only; recorded as a Failure-Arbiter AMBIGUITY resolution.

## Migration Plan

1. Amend `session_7_contract.yaml` `allowed_files` (X-1 files, `.gitignore`,
   `CODE_OF_CONDUCT.md`, `docs/handoff.md`, `docs/eval_corpus/**`, the contract itself).
2. X-1 first (TDD) — it is the only behavioral change and gates the auth story the README
   tells. Run WebUI checks.
3. Hygiene files (LICENSE → SECURITY → CONTRIBUTING → CODE_OF_CONDUCT → templates → release
   checklist), then `.gitignore`.
4. README last, so it can reference the now-present hygiene files and the fixed auth behavior.
5. Update evidence/risk; run full checks; classify failures; sharded review; adversarial
   verification; handoff + eval seeds.

**Rollback:** all deliverables are additive files or a one-line client change; `git restore`
per file reverts cleanly. The X-1 revert is a single line and its tests.

## Open Questions

- **CI badge visibility** — resolves only after the repo is public; tracked as an at-publish
  item in `docs/release_checklist.md` (not blocking for S7). 
- **`docs/model_setup.md` internal default inconsistency** (oracle defaults `COSMOS3_MODEL_DIR`
  to NVFP4 while action/orchestrator default FP8) — README tells operators to set it explicitly;
  the code fix is out of scope (product code; not X-1). Routed to `MIG-S8`/a code session.
