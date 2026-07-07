# Eval Seed - MIG-S7 A Behavioral Fix Leaves a Stale Comment in a Sibling Public File

Session: MIG-S7
Caught by: sharded review (correctness axis, F2)
Severity caught: Medium (a public tracked file contradicted the README + evidence map)

## Prompt Seed

The X-1 fix changed `webui/lib/proxy.ts` to forward `X-API-Key`, so enabling
`COSMOS3_API_KEY` now works end to end. But `.env.example` still carried a comment from the
previous session — "enabling it currently breaks the WebUI→API proxy (Bearer vs X-API-Key
… pre-existing)". The fix's commit did not touch `.env.example` (it was not in the initial
blast radius), so a public, tracked, operator-facing file now stated the OPPOSITE of the
README and the evidence map. A user reading `.env.example` would avoid enabling auth based on
a now-false warning.

The general failure: a behavioral fix falsifies prose ABOUT the old behavior that lives in
sibling files (examples, READMEs, comments), and the fix's own diff doesn't surface them.

## Inputs

- A behavioral change (here `webui/lib/proxy.ts`) plus sibling public files that describe the
  old behavior: `.env.example`, `README.md`, docs, code comments.

## Expected Verifier Behavior

1. After a behavioral fix, grep the tracked public surface for statements about the OLD
   behavior — search for the symptom words, not just the changed file.
   e.g. `rg -n "breaks|broken|currently|mismatch|Bearer|X-API-Key" .env.example README.md docs`.
2. Update every stale statement so public files agree (invariant: public claims match
   evidence). If a stale file is outside the blast radius, amend the radius (owner-reviewed)
   rather than shipping the contradiction — the fix is incomplete until siblings agree.
3. Re-scan for cross-file contradiction before declaring the fix done.

## Regression Command Shape

```bash
# After the fix, no public file may still describe the pre-fix (broken) behavior:
rg -n "currently breaks|Bearer vs" .env.example README.md docs   # expect: none
```

## Expected Result

No tracked public file contradicts the README/evidence about the fixed behavior; `.env.example`
describes the working `X-API-Key` path.

## Promotion Target

- REVIEW.md / project contract template rule: "A behavioral fix is incomplete until sibling
  public files (examples, READMEs, comments) that describe the old behavior are updated;
  grep the symptom terms across the tracked surface, and amend the blast radius if a stale
  file sits outside it."
