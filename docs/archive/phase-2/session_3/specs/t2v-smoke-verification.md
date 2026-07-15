# Capability: T2V Smoke Verification

## ADDED Requirements

### Requirement: Best-effort, non-blocking T2V smoke
The T2V smoke probe SHALL attempt one small, direct-only text-to-video
generation and SHALL record its outcome as `PASS`, `FAIL`, or `SCOPED_OUT`
(never a bare boolean), and its outcome SHALL NOT block or fail the session,
per `session_3.md`'s SHOULD (not MUST) wording for this deliverable.

#### Scenario: T2V succeeds
- **WHEN** a T2V request completes and returns a valid video artifact within
  the probe's VRAM/time budget
- **THEN** the probe records `verdict: PASS` with the artifact's metadata
  (dimensions, frames, fps, duration)

#### Scenario: T2V is infeasible and is scoped out, not silently dropped
- **WHEN** a T2V attempt fails for a resource reason (VRAM exhaustion,
  timeout, unsupported request shape)
- **THEN** the probe SHALL catch the failure and record `verdict:
  SCOPED_OUT` with a `notes` field stating the concrete reason, and this
  scoped-out result SHALL still appear in the session's evidence output —
  it SHALL NOT be omitted or treated as if the task were never attempted

### Requirement: Checkpoint order and resolution budget
The T2V smoke probe SHALL attempt NVFP4 first (lower bit-width leaves more
VRAM headroom for the temporal dimension), at the lowest documented
supported resolution (256, per `docs/model_setup.md` §9's dimension set)
and a minimal frame count, before falling back to FP8 once if NVFP4 does
not fit.

#### Scenario: NVFP4 is tried before FP8
- **WHEN** the T2V smoke probe runs with no checkpoint explicitly forced
- **THEN** it SHALL attempt NVFP4 first; it SHALL only attempt FP8 if the
  NVFP4 attempt records `FAIL` or `SCOPED_OUT`

#### Scenario: 720p and other out-of-scope shapes are never attempted
- **WHEN** the T2V smoke probe selects a request shape
- **THEN** it SHALL NOT request 720p video (PRD/`session_3.md` explicit
  out-of-scope: peak VRAM exceeds 32 GB on the target GPU)

### Requirement: T2I evidence integrity is unaffected by the T2V attempt
The T2V smoke probe SHALL run only after every direct and full-stack T2I
evidence fragment (FP8 and NVFP4) already has a recorded `PASS` or `FAIL`
verdict, and a T2V failure SHALL NOT invalidate, overwrite, or require
re-running any already-recorded T2I evidence fragment.

#### Scenario: T2V destabilizes the container but T2I evidence survives
- **WHEN** the T2V attempt causes the generation container to crash or
  become unresponsive (the contract's own `failure_modes_to_watch` case)
- **THEN** the already-written T2I `evidence_direct_t2i_*.json` and
  `evidence_fullstack_t2i_*.json` fragments SHALL remain on disk unchanged,
  and `aggregate.py` SHALL still be able to merge them into the final
  evidence bundle independent of the T2V outcome
