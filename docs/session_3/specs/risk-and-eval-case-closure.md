# Capability: Risk and Eval Case Closure

## MODIFIED Requirements

### Requirement: Risk register rows close with evidence, not by assumption
**Previous behavior:** `docs/risk_register.md` row R-05 ("T2I/T2V still
fails together for a reason other than drift D1") read "Open -
blueprint-time" with `GPU-S3` as owner. Row R-09 ("RTX 5090 host
unavailable or contended") was closed for `GPU-S1` only, with an explicit
note that `GPU-S3` must re-verify independently.

**New behavior:** R-05 SHALL close with a status citing this session's
actual joint-validation evidence (pass, or the specific new-form failure
found, per the row's own mitigation text) — it SHALL NOT close on the
strength of `GPU-S1` and `GPU-S2` each having passed individually. R-09
SHALL close for `GPU-S3` specifically, citing the independent
`nvidia-smi` re-verification performed at this session's own execution
time (not reusing `GPU-S1`'s idle-GPU observation from a different
session). If joint validation surfaces a new failure mode, this session
SHALL add a new risk row rather than silently reusing or closing R-05
against an unrelated cause.

#### Scenario: R-05 closes on a full pass
- **WHEN** FP8 and NVFP4 T2I both pass (direct and full-stack) and the T2V
  smoke's outcome is recorded either way
- **THEN** R-05's status SHALL change from "Open - blueprint-time" to a
  closed status citing the specific evidence rows in
  `docs/evidence_map.md`

#### Scenario: A new drift form found during this session becomes a new row, not a silent R-05 close
- **WHEN** joint validation surfaces a failure that is neither the
  already-known drift D1 nor a T2I/T2V outcome covered by existing rows
- **THEN** this session SHALL add a new row to `docs/risk_register.md`
  describing it, and SHALL NOT mark R-05 closed while that new failure is
  unresolved

### Requirement: Eval seed cases close with a recorded result, never left ambiguous
**Previous behavior:** `docs/eval_seed_cases.md` rows `EV-GPU-FP8-T2I`,
`EV-GPU-NVFP4-T2I`, `EV-GPU-T2V-SMOKE`, and `EV-GPU-JOBS-ARTIFACT` were
defined with expected properties but no recorded result (gated on
`GPU-S3`).

**New behavior:** each of the four rows SHALL be updated with this
session's actual result — pass, fail, or (for `EV-GPU-T2V-SMOKE` only,
per its SHOULD framing) explicitly scoped out with a reason — and SHALL
reference the checkpoint revisions this session actually used
(`9bf5d6ae164688487bdb71947ccc6ebe70d12900` for FP8,
`5514c42b9759739f545e0d0dee453db8d8525fbc` for NVFP4), never the pre-fix
revisions.

#### Scenario: EV-GPU-JOBS-ARTIFACT closes from full-stack evidence
- **WHEN** either checkpoint's full-stack probe records a job reaching a
  terminal state with a downloadable artifact
- **THEN** `EV-GPU-JOBS-ARTIFACT` SHALL be updated with that result and a
  reference to the backing evidence row

#### Scenario: EV-GPU-T2V-SMOKE closes even when scoped out
- **WHEN** the T2V smoke probe records `SCOPED_OUT` rather than `PASS` or
  `FAIL`
- **THEN** `EV-GPU-T2V-SMOKE` SHALL still be updated to reflect that
  outcome and its reason — it SHALL NOT be left in its pre-session,
  not-yet-run state
