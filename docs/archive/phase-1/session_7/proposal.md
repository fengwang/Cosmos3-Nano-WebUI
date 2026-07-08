# Session 7 Proposal - README, Project Hygiene, and Beta Polish

Date: 2026-07-07
Session: MIG-S7
Risk: medium · Gate: `GATE-MIG-S7-PUBLIC`
Derived from: `docs/session_7/brainstorming.md` (approved 2026-07-07)

## Motivation

The README is the first user interface for the public GitHub repo. It must explain what
Cosmos3-Nano-WebUI is, how to run it **from public inputs only**, what is verified versus
what remains a manual gate, and which licenses apply — without overclaiming. Beta users
also need the community-health files that let them adopt, report, and contribute safely:
`LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue/PR templates, and
a release checklist. Two hygiene defects surfaced by prior sessions are fixed here under an
owner-approved blast-radius amendment: the **X-1** auth-header mismatch (enabling the API
key currently breaks the WebUI→API proxy) and a root `.gitignore` that fails to exclude
build artifacts contributors will now be invited to avoid committing.

## Specific changes agreed

1. **Public `README.md`** — logo, badges (License · Python · Status · CI), one-liner +
   subtitle, research-preview banner, evidence-qualified feature matrix, quickstart
   (local build + public checkpoint download), requirements, external checkpoint setup
   with three-way license separation and a link to `docs/model_setup.md`, development
   setup mirroring CI, limitations/beta status, troubleshooting, and hygiene links.
2. **Community-health files** — `LICENSE` (MIT), `SECURITY.md` (private reporting, not
   public issues), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1),
   `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.yml` + `config.yml`,
   `.github/PULL_REQUEST_TEMPLATE.md`, `docs/release_checklist.md`.
3. **X-1 auth fix** — `webui/lib/proxy.ts` sends `X-API-Key: <key>` (the API's existing
   contract header) instead of `Authorization: Bearer <key>`; tests updated (TDD).
4. **`.gitignore` hardening** — exclude `__pycache__/`, `.venv/`, `node_modules/`, build
   and cache directories, `models/`, and media artifacts.
5. **Docs** — refining pack under `docs/session_7/**`; updates to
   `docs/{evidence_map,risk_register,eval_seed_cases}.md`, `docs/eval_corpus/`,
   `docs/handoff.md`; a noted `allowed_files` amendment in `docs/session_7_contract.yaml`.

## Capabilities (contract with the specification phase)

### New capabilities (one spec file each)

- **`public-readme`** — a public, non-empty README that presents the project with
  evidence-qualified claims (no production/performance claims), a public-only setup flow,
  three-way license separation, links that resolve to tracked files, and a concise
  structure that points to `docs/` for detail.
- **`community-hygiene`** — the community-health file set exists and is safe: MIT
  `LICENSE` scoped to repo code (not weights); `SECURITY.md` routes vulnerabilities to a
  private channel and forbids public disclosure; `CONTRIBUTING.md` uses specific commands
  and mirrors CI; `CODE_OF_CONDUCT.md`; issue/PR templates request no secrets/sensitive
  data; `config.yml` disables blank issues; `docs/release_checklist.md` gates beta.
- **`bff-auth-header`** — the WebUI BFF forwards the API key on the header the API
  enforces (`X-API-Key`), so enabling `COSMOS3_API_KEY` authenticates instead of `401`-ing;
  the browser cannot spoof or read the key.

### Modified capabilities

- **`repo-ignore-hygiene`** (MODIFIED) — the root `.gitignore` gains standard
  language/build/artifact excludes while continuing to ignore the existing local-only
  files (`references/`, `AGENTS.md`, `CLAUDE.md`, `ENVIRONMENTS.md`, `REVIEW.md`,
  `docs/agent_workflow/`) and never newly ignoring a currently-tracked path.

## Impact

- **Affected files (new):** `README.md` (populated), `LICENSE`, `SECURITY.md`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `.github/ISSUE_TEMPLATE/**`,
  `.github/PULL_REQUEST_TEMPLATE.md`, `docs/release_checklist.md`, `docs/session_7/**`,
  `docs/eval_corpus/mig_s7_*.md`.
- **Affected files (modified):** `webui/lib/proxy.ts`, `webui/lib/proxy.test.ts`,
  `webui/lib/proxyFetch.test.ts` (X-1); `.gitignore`; `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/handoff.md`,
  `docs/session_7_contract.yaml` (amendment).
- **APIs:** the public API request shape is **unchanged** — `X-API-Key` remains the
  contract; only the internal BFF client is corrected (`INV-9` preserved). No route,
  method, or schema change.
- **Dependencies:** none added (`INV-10`). Docs and config only, plus a one-line client
  header change.
- **Systems:** enabling `COSMOS3_API_KEY` now protects the job/artifact routes end to end
  (partially mitigates **R-16** by making auth actually usable). No runtime feature is
  added; GPU inference remains the `MIG-S8` gate.
