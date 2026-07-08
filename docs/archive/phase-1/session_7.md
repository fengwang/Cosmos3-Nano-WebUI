# Session 7 - README, Project Hygiene, and Beta Polish

Contract: `docs/session_7_contract.yaml`
Risk: medium
Routing: worker_plus_reviewers

## Objective

Write the public README and add project hygiene files needed for a credible
public beta.

## Why This Session Exists

The README is the first user interface for the GitHub repo. It must explain what
the project does, how to run it from public inputs, what is verified, what remains
manual, and which licenses apply.

## In Scope

1. Write README with logo, concise pitch, badges, feature summary, quickstart,
   requirements, external checkpoint setup, Docker setup, development setup,
   limitations, and troubleshooting.
2. Use evidence-qualified language for FP8, NVFP4, RTX 5090, and performance.
3. Add `LICENSE` with MIT text for repo code.
4. Add `SECURITY.md`, `CONTRIBUTING.md`, issue templates, and a release checklist.
5. Confirm README links and commands match files from `MIG-S3` through `MIG-S6`.
6. Keep README concise and move detailed material to docs when needed.

## Out of Scope

- No new runtime features.
- No Docker publishing.
- No model-card editing outside this repo unless separately approved.
- No production-readiness claim.

## Deliverables

- Public `README.md`.
- `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, issue templates, release checklist.
- Link and claim review notes.
- Updated evidence/risk rows for public docs.

## Deterministic Checks

```bash
rtk rg -n "$PRIVATE_REF_PATTERN" README.md docs .github
rtk rg -n "production-ready|guaranteed|always|official" README.md docs
rtk test -f LICENSE
rtk test -f SECURITY.md
rtk test -f CONTRIBUTING.md
```

Use a link checker if one is already available in the repo; do not add a new
production dependency only for link checking.

## Exit Criteria

- `GATE-MIG-S7-PUBLIC` passes.
- README setup flow is public-only and consistent with current files.
- Hygiene files exist.
- Public claims match the evidence map.

## Handoff

Hand off the README claim matrix, hygiene file list, unresolved docs gaps, and
release checklist to `MIG-S8`.
