# Eval Seed - MIG-S2 Private Source Scrub

Session: MIG-S2
Caught by: sharded review
Severity caught: High

## Prompt Seed

After a session writes planning, evidence, handoff, or review docs for a public
GitHub migration, scan the changed public docs for private source details.

## Inputs

- Public docs under `docs/session_*/`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/handoff.md`

## Expected Verifier Behavior

The verifier MUST fail the session if public docs contain real private source
checkout paths, private branch names, private source commit hashes, private
hosts, secrets, or local-only artifact references. It MUST allow policy language
that describes the rule without naming the private value.

## Regression Command Shape

```bash
rtk rg -n "<known private path pattern>|<known private branch pattern>|<known private source hash pattern>" docs/session_* docs/evidence_map.md docs/risk_register.md docs/handoff.md
```

## Expected Result

No matches for real private values. If matches exist, classify as BUG against
PRD FR-2/NFR-1 and `docs/project_contract.md` INV-1, then scrub before handoff.
