# Capability: Per-Mode Verification Status Reporting

## MODIFIED Requirements

### Requirement: Per-mode markings reflect evidenced GPU verification status
**Previous behavior:** `README.md`'s capability table, `docs/model_setup.md`
§6 (per-mode compatibility matrix) and §8 (operator setup), and
`docs/release_checklist.md` §7 marked every generation mode
(`t2v`/`t2v_audio`/`i2v`/`t2i`), reasoning, and action/`forward_dynamics` as
"GPU-unverified" uniformly, regardless of what evidence actually existed.

**New behavior:** `README.md`, `docs/model_setup.md` §6/§8, and
`docs/release_checklist.md` §7 SHALL mark FP8 and NVFP4 `t2i` as
"T2I-verified" if and only if this session's evidence records a `PASS`
verdict for that checkpoint's direct AND full-stack generation probes.
Every other mode (`t2v`, `t2v_audio`, `i2v`, reasoning, action/
`forward_dynamics`) SHALL remain marked "GPU-unverified", since none of
them are in this session's scope. Every marking change SHALL cite the
`docs/evidence_map.md` row backing it (`project_contract.md` §7: "Claims...
must point to an evidence row... or be phrased as a limitation").

If either checkpoint's T2I evidence records `FAIL` instead of `PASS`, that
checkpoint's `t2i` marking SHALL stay "GPU-unverified" and the failure SHALL
be recorded as a limitation rather than silently left ambiguous.

#### Scenario: Both checkpoints pass — markings upgrade
- **WHEN** this session's evidence shows `PASS` for FP8 and NVFP4 across
  both direct and full-stack T2I
- **THEN** `README.md`, `docs/model_setup.md`, and
  `docs/release_checklist.md` each upgrade their FP8/NVFP4 `t2i` marking to
  "T2I-verified", each citing the corresponding `docs/evidence_map.md` row

#### Scenario: One checkpoint fails — its marking does not upgrade
- **WHEN** NVFP4's full-stack T2I evidence records `FAIL`
- **THEN** NVFP4's `t2i` marking SHALL remain "GPU-unverified" in all three
  documents, and the failure and its cause SHALL be recorded as a limitation
  (not silently omitted), while FP8's marking upgrades independently if its
  own evidence is `PASS`

#### Scenario: Out-of-scope modes are untouched
- **WHEN** the per-mode markings are updated after this session
- **THEN** `t2v`, `t2v_audio`, `i2v`, reasoning, and action/
  `forward_dynamics` markings SHALL be unchanged from their pre-session
  text, since none of them were validated this session (the T2V smoke is
  tracked separately and does not by itself upgrade a "verified" marking)
