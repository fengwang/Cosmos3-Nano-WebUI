# Eval Seed - MIG-S3 Curated-Import Completeness (No Hollow Pass)

Session: MIG-S3
Caught by: design + deterministic checks (import graph); confirmed by adversarial verifier
Severity caught: High (would-be, if import were incomplete)

## Prompt Seed

After a curated source import that excludes some modules/tests, the CPU test suite
can pass GREEN simply because a critical module was never imported (the
`session_3_contract.yaml` adversarial case "Imported tests pass only because
critical modules were not imported").

## Inputs

- The imported tree (`api/`, `tools/`, `tests/`)
- The include/exclude manifest (`docs/session_{n}/import_manifest.md`)

## Expected Verifier Behavior

The verifier MUST prove the kept import graph is complete, not just that tests pass:

1. `python -m compileall api` exits 0.
2. Torch-free `PYTHONPATH=api python -c "import app.main"` exits 0 (the app builds
   from imported modules only).
3. `pytest -m "not gpu"` passes AND actually exercises product code — verify by
   inverting one core behavior (e.g. a readiness/validation gate) in a scratch copy
   and confirming a real test FAILS. A suite that stays green under an inverted gate
   is hollow.
4. No kept file imports an excluded module (e.g. `engines.trtllm`, the `equivalence`
   harness).

## Regression Command Shape

```bash
PYTHONPATH=api python -c "import app.main"
python -m pytest -m "not gpu" -q
rg -n "engines\\.trtllm|from equivalence|import equivalence" api tests tools
```

## Expected Result

Import + compile succeed, the suite passes and is non-hollow (inverted-gate check
fails at least one test), and no kept code references an excluded module. If a kept
test imports an excluded module, classify as AMBIGUITY (exclude the test with the
excluded code) or BUG (the module was needed and should not have been excluded).

## Promotion Target

Add a CI check (MIG-S5): torch-free `import app.main` + `pytest -m "not gpu"` +
an excluded-module import grep, run on every import/curation change.
