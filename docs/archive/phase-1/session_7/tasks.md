# Session 7 Tasks - README, Project Hygiene, and Beta Polish

Session: MIG-S7
Derived from: `specs/*.md` (what) + `design.md` (how)

## 1. Contract amendment

- [ ] 1.1 Amend `docs/session_7_contract.yaml` `allowed_files` to add
      `webui/lib/proxy.ts`, `webui/lib/proxy.test.ts`, `webui/lib/proxyFetch.test.ts`
      (X-1), `.gitignore`, `CODE_OF_CONDUCT.md`, `docs/handoff.md`,
      `docs/eval_corpus/**`, and `docs/session_7_contract.yaml`. Record owner approval
      (2026-07-07) inline. Spec: all (enabling change).

## 2. X-1 auth header fix (TDD, behavioral)

- [ ] 2.1 Update `webui/lib/proxy.test.ts` and `webui/lib/proxyFetch.test.ts` to expect
      `x-api-key` (RED against current `Bearer` code) — spec `bff-auth-header`.
- [ ] 2.2 Change `webui/lib/proxy.ts` to `out.set("x-api-key", apiKey)` (GREEN) — spec
      `bff-auth-header`.
- [ ] 2.3 Verify: `pnpm test`, `pnpm lint`, `pnpm typecheck` in `webui/` all pass.

## 3. Community-health files

- [ ] 3.1 Add `LICENSE` (MIT text + copyright) — spec `community-hygiene`.
- [ ] 3.2 Add `SECURITY.md` (private reporting; forbids public issues; beta posture) —
      spec `community-hygiene` (D-6).
- [ ] 3.3 Add `CONTRIBUTING.md` (specific commands, mirrors CI, links CoC) — spec
      `community-hygiene`.
- [ ] 3.4 Add `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1) — spec `community-hygiene`.
- [ ] 3.5 Add `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.yml` + `config.yml`
      (no sensitive-data fields; `blank_issues_enabled: false`; security redirect) —
      spec `community-hygiene`.
- [ ] 3.6 Add `.github/PULL_REQUEST_TEMPLATE.md` — spec `community-hygiene`.
- [ ] 3.7 Add `docs/release_checklist.md` (pre-beta gate) — spec `community-hygiene`.

## 4. Repository ignore hygiene

- [ ] 4.1 Harden root `.gitignore` (Python/Node/build/cache/model/media excludes; retain
      pre-existing local-only ignores) — spec `repo-ignore-hygiene` (D-8).
- [ ] 4.2 Verify: `git check-ignore` reports the new artifacts ignored; no tracked file
      becomes ignored; `git status` stays clean.

## 5. Public README

- [ ] 5.1 Write `README.md` — logo, badges (License/Python/Status/CI), pitch, research
      preview banner, evidence-qualified feature matrix, quickstart (local build + public
      download), requirements, checkpoint setup (license separation + link to
      `docs/model_setup.md`), development setup (mirrors CI), limitations/beta status,
      troubleshooting, hygiene links — spec `public-readme` (D-1..D-4, D-7, D-9).
- [ ] 5.2 Verify: `test -s README.md`; forbidden-claims scan over `README.md` returns no
      unsupported claim; every relative link target is tracked (`git ls-files`).

## 6. Verification and review

- [ ] 6.1 Run all contract deterministic checks (presence, private-ref scanner,
      forbidden-claims over S7 deliverables, WebUI checks); classify any failure via the
      Failure Arbiter; save `docs/session_7/failure_arbiter.md`.
- [ ] 6.2 Sharded review (correctness / security / tests / architecture / performance);
      save `docs/session_7/sharded_review.md`; fix only High/Critical; re-check.
- [ ] 6.3 Adversarial verification (fresh context; contract + diff + evidence only);
      save `docs/session_7/adversarial_verification.md`.

## 7. Close

- [ ] 7.1 Update `docs/evidence_map.md` (S7 row), `docs/risk_register.md`
      (R-01/R-09/R-11/R-15/R-16 + X-1 closure), `docs/eval_seed_cases.md`; add
      `docs/eval_corpus/mig_s7_*.md` seeds.
- [ ] 7.2 Verify the done condition (`GATE-MIG-S7-PUBLIC`); write/update `docs/handoff.md`
      (README claim matrix, hygiene file list, link-check notes, remaining docs gaps,
      release checklist pointer); state remaining risks and next-session warnings.

## Ordering / dependencies

1 (amendment) unblocks the out-of-original-radius edits (2, 4, `CODE_OF_CONDUCT.md`).
2 (X-1) is done first among edits because it is the only behavioral change and the README's
auth story depends on it. 3 and 4 are independent file additions. 5 (README) is last so it
can reference the now-present hygiene files and the fixed auth behavior. 6 runs after 1–5
land. 7 closes after 6. Commit at clean checkpoints per task group if requested.
