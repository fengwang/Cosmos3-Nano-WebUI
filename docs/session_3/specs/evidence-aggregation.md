# Capability: Evidence Aggregation

## ADDED Requirements

### Requirement: Pure fragment merge
`aggregate.py` SHALL merge every `docs/session_3/probes/evidence_*.json`
fragment into one `docs/session_3/probes/evidence.json` and a
human-readable `docs/session_3/probes/summary.md`, using a pure merge
function: the same set of fragment contents SHALL always produce the same
merged output, with no network, filesystem, or clock access inside the
merge logic itself (file reads/writes stay in a thin action wrapper around
it).

#### Scenario: Aggregation is deterministic
- **WHEN** `aggregate.py` is run twice against the same set of fragment
  files with no changes between runs
- **THEN** both runs SHALL produce byte-identical `evidence.json` content
  (modulo an explicit, separately-parameterized timestamp field, if any)

### Requirement: Partial results aggregate without blocking on missing tasks
`aggregate.py` SHALL merge whatever fragments exist at the time it is run
and SHALL NOT fail or refuse to produce output solely because a fragment
for a not-yet-attempted or intentionally-skipped task is absent; it SHALL,
however, clearly list which of the session's expected task IDs have no
corresponding fragment.

#### Scenario: Aggregation runs after only T1-T6 have fragments
- **WHEN** `aggregate.py` is run before the T2V smoke probe has produced
  `evidence_t2v_smoke.json`
- **THEN** it SHALL still produce a valid `evidence.json` covering T1-T6 and
  SHALL list `T7 (t2v-smoke)` as missing/not-yet-run, rather than raising an
  error or silently omitting the gap

### Requirement: Aggregated summary is traceable to INV-8 fields
`summary.md` SHALL present, for every fragment, at minimum the checkpoint
repo+revision, the vLLM-Omni commit, the request shape, and the verdict —
enough for a reader to independently confirm the evidence satisfies
`project_contract.md` INV-8 without opening the raw JSON.

#### Scenario: A reviewer can audit pass/fail from summary.md alone
- **WHEN** a sharded reviewer or adversarial verifier reads
  `docs/session_3/probes/summary.md`
- **THEN** every task's checkpoint revision, vLLM-Omni commit, request
  shape, and verdict SHALL be visible without cross-referencing the raw
  `evidence_*.json` fragments
