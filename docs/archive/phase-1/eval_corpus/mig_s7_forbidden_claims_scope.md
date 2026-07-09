# Eval Seed - MIG-S7 Forbidden-Claims Scan Over-Matches the Whole Doc Tree

Session: MIG-S7
Caught by: baseline check + Failure Arbiter (FA-2, AMBIGUITY)
Severity caught: Medium (a literal reading would demand out-of-blast-radius edits)

## Prompt Seed

The contract's claim gate is `rg -n "production-ready|guaranteed|always|official" README.md
docs`. Run literally over the whole `docs/` tree it returns ~20 matches that are NOT
unsupported claims: negations (`prd.md` "not production-ready"), casual English
("always-heavy", "always-on", "always build first"), the standard Contributor Covenant text
("officially representing", "official e-mail address"), and — recursively — the check's own
regex quoted inside `session_7.md`, the contract, and the session docs. Most matched files
are outside the S7 blast radius (`prd.md`, `session_5/**`, `session_6/**`). A verifier that
treats "zero matches anywhere" as the gate would either fail a clean session or edit
change-controlled files to satisfy a lint proxy.

## Inputs

- `docs/session_7_contract.yaml` acceptance criterion: "Claim review finds no unsupported
  production or performance claims" + deterministic check `rg … README.md docs`.
- The whole `docs/` tree (pre-existing prose from prior sessions) + the new S7 deliverables.

## Expected Verifier Behavior

1. Read the regex as a HEURISTIC for the real criterion ("no unsupported production or
   performance claims"), not as "zero matches under docs".
2. Enforce zero *claim* matches over the SESSION DELIVERABLES (README, new hygiene files,
   `docs/session_7/**`, evidence/risk edits); classify each match as (a) a real
   production/performance claim vs (b) negation / casual English / standard external text /
   the check's own regex.
3. Leave pre-existing out-of-blast-radius matches untouched (change control).
4. Record the disposition as a Failure-Arbiter AMBIGUITY, not a silent pass or a
   scope-violating edit.

## Regression Command Shape

```bash
rg -n "production-ready|guaranteed|always|official" README.md   # zero in the README itself
# then classify any match under docs/session_7 + the new hygiene files; none may be a claim
```

## Expected Result

`README.md` has zero forbidden-claim tokens; every match elsewhere in the S7 deliverables is
category-(b) and documented; no out-of-radius file is edited to satisfy the literal scan.

## Promotion Target

- REVIEW.md / project contract template rule: "Lexical claim gates are heuristics scoped to
  the session's deliverables; classify matches (claim vs negation/boilerplate/check-text)
  rather than requiring a whole-tree zero-match, and never edit change-controlled files to
  silence the proxy."
- Optional check refinement: scope the forbidden-claims `rg` to the changed files
  (`git diff --name-only`) intersected with `README.md`/`docs`, and allow-list the check's
  own definition lines.
