# Session 1 Proposal

## Motivation

Cosmos3-Nano-WebUI is moving from a private development context to a public beta repo. Before source code, Docker, CI, or README work begins, later sessions need a public-safe baseline: what exists in the public repo, which public remotes matter, which files may be imported, which files must stay out, and which scrub checks block release.

## Agreed Changes

- Create a Session 1 lifecycle pack under `docs/session_1/`.
- Record the current public repo baseline in `docs/session_1/inventory.md`.
- Define allowed future import categories in `docs/session_1/import_manifest.md`.
- Define excluded files and path classes in `docs/session_1/exclusion_manifest.md`.
- Define repeatable scrub commands in `docs/session_1/scrub_checklist.md`.
- Update `docs/evidence_map.md`, `docs/risk_register.md`, and `docs/eval_seed_cases.md` only when current evidence requires it.
- Write `docs/handoff.md` at session end under the user's explicit blast-radius amendment.
- Commit after each completed task checkpoint.

## Capabilities

### New Capabilities

1. **Public Repository Inventory**
   - Records branch, commit, status, remotes, file tree, current docs state, and baseline command evidence.
2. **Target Remote Baseline**
   - Records public target remotes for the WebUI repo, vLLM-Omni fork, and Hugging Face checkpoint repos.
3. **Curated Import Manifest**
   - Defines what future sessions may import into the public repo.
4. **Exclusion Manifest**
   - Defines what future sessions must exclude by default.
5. **Private-Reference Scrub Checklist**
   - Defines scrub patterns, commands, and expected results for private references, secrets, weights, generated media, and legacy submodules.
6. **Evidence, Risk, And Handoff Bookkeeping**
   - Keeps evidence/risk docs aligned with observed baseline facts and hands Session 1 outputs to later sessions.

### Modified Capabilities

No public product capabilities change in this session. The only modified repository behavior is documentation process state: `docs/handoff.md` becomes an allowed Session 1 output by direct user amendment.

## Impact

- Affected docs:
  - `docs/session_1/**`
  - `docs/evidence_map.md` if baseline evidence changes
  - `docs/risk_register.md` if risk status changes
  - `docs/eval_seed_cases.md` if eval seeds need expansion
  - `docs/handoff.md` by user amendment
- Affected APIs: none.
- Affected runtime source: none.
- Affected dependencies: none.
- Affected systems: future migration sessions consume the manifests and scrub checklist.
