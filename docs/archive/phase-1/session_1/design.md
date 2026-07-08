# Session 1 Design

## Context

Session 1 is the public migration boundary-setting session. The repo currently contains blueprint documentation, an empty `README.md`, and `misc/logo.png`; it does not contain the runtime source tree. The PRD and project contract require public evidence only, external model weights, no private paths, and no source import during this session.

The session contract is low risk and single-agent. The user amended the allowed file set to include `docs/handoff.md` for the final handoff.

## Goals

- Record the public repo baseline in a form later sessions can verify.
- Define import rules for `MIG-S3`.
- Define exclusion rules that prevent private or bulky files from entering the public repo.
- Define scrub commands that later sessions can run without knowing private context.
- Keep evidence and risk docs honest about what Session 1 proves.
- Commit each completed task checkpoint.

## Non-Goals

- No source import.
- No vLLM-Omni rebase.
- No Docker changes.
- No README rewrite.
- No GPU validation.
- No checkpoint validation beyond listing public target repo IDs.
- No product API or WebUI behavior changes.

## Decisions

### Decision 1: Split Operator Artifacts

Use separate files for inventory, import manifest, exclusion manifest, and scrub checklist.

Rationale: `MIG-S2` needs remote and handoff context, while `MIG-S3` needs import, exclusion, and scrub rules. Separate files reduce ambiguity.

Rejected alternative: one combined scope note. It is shorter but weaker for future execution.

### Decision 2: Treat Scrub Rules As Data

The scrub checklist will define named pattern groups and commands. `$PRIVATE_REF_PATTERN` is allowed when set, but the checklist must include a fallback pattern because it is unset in the current shell.

Rationale: the contract command is useful, but a later worker needs a command that works from a clean shell.

Rejected alternative: only record the failed environment variable check. That would not give future sessions a usable scrub baseline.

### Decision 3: Evidence Updates Stay Minimal

Only update `docs/evidence_map.md`, `docs/risk_register.md`, or `docs/eval_seed_cases.md` when observed Session 1 evidence changes or sharpens the current baseline.

Rationale: these docs already hold blueprint-time facts. Session 1 should not rewrite unrelated rows.

Rejected alternative: rewrite the evidence and risk docs from scratch. That would exceed the session's narrow purpose.

### Decision 4: Documentation Checks Are The Test Surface

Use deterministic shell checks instead of application tests because this session creates documentation and policy artifacts, not runtime code.

Rationale: file existence, heading checks, scan commands, and blast-radius checks directly test the Session 1 specs.

## ACD Boundary

- Actions: run `git`, `rg`, and remote probes; write files; commit checkpoints.
- Calculations: classify observed files into import or exclusion categories; decide whether evidence/risk docs need updates; classify failures before fixes.
- Data: command outputs, commit IDs, remote URLs, manifest entries, scrub pattern groups.

This keeps volatile shell evidence at the edge and records the durable results as plain Markdown.

## Risks And Mitigations

- `$PRIVATE_REF_PATTERN` is unset. Mitigation: record it as an environment/setup gap and define a fallback command set.
- Import rules could block runtime files needed later. Mitigation: phrase the import manifest as categories with proof requirements, not a hard path whitelist from a source tree that is not present yet.
- Exclusion rules could be too vague. Mitigation: list file classes, extensions, path fragments, and release-blocking scans.
- Evidence rows could overstate proof. Mitigation: distinguish observed public baseline from future release gates.
- Scope could drift into source import. Mitigation: keep all writes inside `docs/session_1/**`, allowed evidence/risk/eval docs, and `docs/handoff.md`.

## Migration Plan

1. Create lifecycle planning artifacts and specs.
2. Create `inventory.md` from deterministic baseline checks.
3. Create `import_manifest.md` and `exclusion_manifest.md`.
4. Create `scrub_checklist.md` and run the baseline scans.
5. Update evidence, risk, eval seed, and handoff docs only as needed.
6. Run final checks and verify `GATE-MIG-S1-SCOPE`.

Rollback is simple: revert the Session 1 commits. No runtime source or dependency state changes.

## Open Questions

None remain for Session 1 execution. The user approved the only blast-radius amendment and selected commit/checkpoint behavior.
