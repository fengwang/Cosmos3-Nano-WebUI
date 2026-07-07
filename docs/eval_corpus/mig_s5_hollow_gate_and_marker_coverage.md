# Eval Seed - MIG-S5 Hollow "Zero-Findings" Gates and Unmarked-Marker Guards

Session: MIG-S5
Caught by: sharded review (tests axis)
Severity caught: Medium (unverified guards / hollow-pass risk)

## Prompt Seed

Two coverage traps a green suite can hide:

1. **Hollow "absence" gate.** A gate whose pass condition is "scan found nothing"
   (`assert scan_tree() == []`) passes GREEN even if the underlying walk visited
   nothing — wrong root, everything excluded, or a swallowed `OSError`. The green
   then reflects zero coverage, not a clean repo.
2. **Unmarked marker guard.** A collection hook that skips `@pytest.mark.gpu` tests
   off-GPU has zero committed coverage when no `gpu`-marked test exists, so a
   regression in the guard (wrong keyword, broken truthy parse) fails silently.

## Inputs

- `tests/test_private_ref_scan.py` (the absence gate)
- `tests/conftest.py` (the gpu-marker collection guard)

## Expected Verifier Behavior

1. For the absence gate: assert the walk visits a **known** committed file and that
   an **end-to-end** planted positive (a concat-built secret / a weight file in a
   synthetic tree) is detected — so the gate provably ran and would fail on a real hit.
2. For the marker guard: unit-test the decision function (truthy env parse) and the
   collection hook with fake items — `gpu` item skipped off-opt-in (reason names the
   env var), non-`gpu` item untouched, `gpu` item runs when opted in.

## Regression Command Shape

```bash
uv run pytest tests/test_private_ref_scan.py tests/test_gpu_marker_policy.py -q
# includes: walks-nonempty, end-to-end planted-secret/weight, and the 3 guard tests
```

## Expected Result

The absence gate has a companion coverage assertion; the marker guard has committed
tests even though no `gpu`-marked test exists yet.

## Promotion Target

Candidate REVIEW.md rule: a gate whose green state means "no findings" MUST carry an
explicit coverage assertion (it ran + fails on a planted positive); a marker/skip
guard MUST have a committed unit test even before any marked test exists.
