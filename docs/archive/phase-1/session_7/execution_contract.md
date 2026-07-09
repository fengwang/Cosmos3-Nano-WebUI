# Session 7 Execution Contract - README, Project Hygiene, and Beta Polish

Session: MIG-S7
Risk: medium · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S7-PUBLIC`

## Planned file changes

Created:
- `README.md` (populated), `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`,
  `.github/ISSUE_TEMPLATE/config.yml`, `.github/PULL_REQUEST_TEMPLATE.md`
- `docs/release_checklist.md`
- `docs/session_7/{brainstorming,proposal,design,tasks,plan,execution_contract}.md`,
  `docs/session_7/specs/{public-readme,community-hygiene,bff-auth-header,
  repo-ignore-hygiene}.md`
- `docs/session_7/{failure_arbiter (if any),sharded_review,adversarial_verification}.md`
- `docs/eval_corpus/mig_s7_*.md`

Modified:
- `webui/lib/proxy.ts`, `webui/lib/proxy.test.ts`, `webui/lib/proxyFetch.test.ts` (X-1)
- `.gitignore`
- `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
  `docs/handoff.md`
- `docs/session_7_contract.yaml` (`allowed_files` amendment — owner-approved 2026-07-07)

## Allowed blast radius

Permitted (contract `allowed_files`): `README.md`, `LICENSE`, `SECURITY.md`,
`CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/**`, `.github/PULL_REQUEST_TEMPLATE.md`,
`docs/release_checklist.md`, `docs/session_7/**`, `docs/evidence_map.md`,
`docs/risk_register.md`.

Amendment (owner-approved this session, recorded in `session_7_contract.yaml`): add
`webui/lib/proxy.ts`, `webui/lib/proxy.test.ts`, `webui/lib/proxyFetch.test.ts` (X-1 fix),
`.gitignore`, `CODE_OF_CONDUCT.md`, `docs/handoff.md`, `docs/eval_corpus/**`,
`docs/session_7_contract.yaml`. Running (not editing) `tests/test_private_ref_scan.py` is
in-bounds.

Forbidden (stop if a change seems required): any `api/**` source (the API auth contract
`X-API-Key` is honored, not changed — `INV-9`); `webui/**` beyond the three named files;
model-weight/media files; `schemas/openapi.json`; Docker publishing workflows; GitHub
secrets; `pyproject.toml`/`uv.lock`/`package.json` dependency pins (no new dependency —
`INV-10`); model-card edits outside this repo. No production-readiness claim.

## First test to write

The X-1 header assertion, updated **before** the source changes (spec `bff-auth-header`):
```bash
cd webui && pnpm test    # baseline after editing the test: FAILS
```
`webui/lib/proxy.test.ts` asserts `out.get("x-api-key") === "secret"` and
`out.get("authorization") === null`; `webui/lib/proxyFetch.test.ts` asserts the upstream
request carries `x-api-key: s3cret`. Against the current `proxy.ts` (which sets
`Authorization: Bearer`), these FAIL. After the one-line source change they pass. The
standing documentation gates are the presence + private-reference + forbidden-claims
scans:
```bash
test -s README.md && test -f LICENSE && test -f SECURITY.md && test -f CONTRIBUTING.md
uv run python tests/test_private_ref_scan.py                                  # 0 findings
rg -n "production-ready|guaranteed|always|official" README.md                 # none as a claim
```

## Checks to run after each task

- **X-1:** `cd webui && pnpm test && pnpm lint && pnpm typecheck` → all pass; the header
  assertions cover the fix.
- **Presence:** `test -s README.md`; `test -f {LICENSE,SECURITY.md,CONTRIBUTING.md,
  CODE_OF_CONDUCT.md}`; issue/PR templates + `docs/release_checklist.md` exist.
- **Private-reference scan:** `uv run python tests/test_private_ref_scan.py` → 0 findings
  (scans `.github`/`docs`/source; covers README + hygiene). A `$PRIVATE_REF_PATTERN`
  fallback `rg` over `README.md docs .github` (unset pattern → S1 baseline, ENVIRONMENT).
- **Forbidden-claims (interpreted):** `rg -n "production-ready|guaranteed|always|official"`
  over the S7 deliverables (`README.md`, new hygiene files, `docs/session_7/**`, and the
  evidence/risk edits) → each match reviewed; none may function as an unsupported
  production or performance claim. Whole-tree pre-existing matches are out of radius and
  documented as a Failure-Arbiter AMBIGUITY resolution.
- **`.gitignore`:** `git ls-files | git check-ignore --stdin` finds no tracked path;
  `git check-ignore` reports the new artifact globs ignored; `misc/logo.png` NOT ignored;
  `git status` clean.
- **Links:** every relative link target in `README.md` (and cross-doc links) resolves via
  `git ls-files --error-unmatch`.

## Review axes to run at the end

correctness · security · tests · architecture · performance (per
`docs/agent_workflow/prompts/sharded_review.md`). Each reviewer read-only; reports
severity + evidence (file/line) + violated clause/invariant + smallest safe fix +
confidence. Fix only High/Critical; re-run checks after fixes. Security reviewer weights:
the X-1 header change (no spoof/leak), `SECURITY.md` disclosure routing, and issue
templates requesting no sensitive data.

## Adversarial verifier brief

Fresh context; sees only `docs/session_7_contract.yaml`, `docs/project_contract.md`, the
session diff, and the evidence — not this conversation. Task: falsify
"`GATE-MIG-S7-PUBLIC` passes with public-facing docs and hygiene ready for release
review." Specifically attempt the contract's adversarial cases: (a) the README claims GPU
support is shipped without manual evidence; (b) the MIT `LICENSE` appears to cover the HF
model weights; (c) the quickstart depends on an unpublished image or a private/absolute
path; (d) security reporting asks users to disclose vulnerabilities in a public issue;
plus (e) the X-1 change alters the public API request shape or lets the client spoof/leak
the key; (f) a private path/host/secret leaked into any deliverable; (g) `.gitignore`
newly ignores a tracked file; (h) a forbidden-claims token functions as an unsupported
claim in an S7 deliverable; (i) a README relative link does not resolve to a tracked file.
Any confirmed item fails the session and routes through the Failure Arbiter.

## Concrete done condition

`GATE-MIG-S7-PUBLIC` is satisfied when all hold, each backed by command evidence:
1. `README.md` is non-empty, embeds the logo, and presents the project with an
   evidence-qualified feature matrix and a beta / research-preview posture up front.
2. Every runtime claim (GPU, FP8/NVFP4, RTX 5090, generation/reasoning/action) is
   qualified as GPU-unverified (the `MIG-S8` gate); no production-readiness or performance
   claim is present.
3. The quickstart runs from public inputs only — clone, public `huggingface-cli` download
   at pinned revisions, local `make build` — with no registry image and no private/absolute
   path.
4. Three-way license separation (repo MIT vs weights `openmdw-1.0` vs base `other`) is
   stated where weights appear, and MIT is not represented as covering the weights.
5. `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, the issue/PR
   templates, and `docs/release_checklist.md` exist; `SECURITY.md` routes to a private
   channel and forbids public-issue disclosure; templates request no sensitive data.
6. X-1 is fixed: the WebUI BFF forwards `X-API-Key`; `pnpm test`/`lint`/`typecheck` pass;
   the API request shape is unchanged (`INV-9`); the key cannot be spoofed or leaked.
7. `.gitignore` excludes build/env/model artifacts and newly ignores no tracked file.
8. Private-reference scan is clean over the new surface; forbidden-claims review is clean
   over the deliverables; all README relative links resolve to tracked files.
9. Sharded review has no unresolved High/Critical; the adversarial verifier passes.
10. `docs/handoff.md` hands `MIG-S8` the README claim matrix, the hygiene file list, the
    link-check notes, the remaining docs gaps, and the release-checklist pointer.
