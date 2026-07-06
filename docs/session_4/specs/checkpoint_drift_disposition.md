# Specification - Checkpoint Drift Disposition

Session: MIG-S4
Capability: Checkpoint Drift Disposition

## ADDED Requirements

### Requirement: Every drift has an owner disposition and a routed risk row

`docs/session_4/drift_report.md` MUST record each drift between the public artifacts
and runtime assumptions with a unique ID, a severity, an explicit owner disposition,
and a reference to the risk-register row that carries it forward. No drift may be left
undispositioned before Docker (S6) or README (S7) depend on it.

#### Scenario: Drift report enumerates dispositions and risk rows

WHEN `docs/session_4/drift_report.md` is read
THEN each drift SHALL have an ID, severity, disposition, and a routed risk row
AND no drift SHALL be marked open without a named owner session.

### Requirement: NVFP4 to FP8 metadata asymmetry is captured

The verification MUST capture the metadata asymmetry between the public FP8 and NVFP4
repos (for example a top-level `quantization_config.json`, `quantizer_map_diff.json`,
`transformer/modelopt_state.pt`, or shipped loader scripts present in one but not the
other) and analyze its loader impact.

#### Scenario: Asymmetry drift D1 documents loader impact

WHEN `docs/session_4/drift_report.md` is read
THEN drift D1 SHALL list the files present in one public repo and absent in the other
AND SHALL state whether the diffusers loader path still resolves for NVFP4
AND SHALL route the disposition to a risk row.

### Requirement: Non-public BF16 base model is captured

The verification MUST record that the BF16 base model required by the reasoner and the
action/forward_dynamics graft is not among the public repos, and MUST route the
affected modes as beta-limited.

#### Scenario: Base-model drift D2 marks modes beta-limited

WHEN `docs/session_4/drift_report.md` is read
THEN drift D2 SHALL record the base repo reachability as NOT_FOUND
AND SHALL mark reasoning and action/forward_dynamics beta-limited
AND SHALL route the disposition to a risk row (R-03 / R-08).

### Requirement: External-repo hygiene is captured without reproducing contents

If the public repos contain dev-process or scratch files, or shipped loader scripts
asymmetric between repos, the verification MUST record their existence and recommend an
external cleanup follow-up. It MUST NOT reproduce the contents of those files in this
repo's docs (they may carry private context).

#### Scenario: Hygiene drift D3 records existence and recommends cleanup

WHEN `docs/session_4/drift_report.md` is read
THEN drift D3 SHALL note the presence of dev-scratch or asymmetric loader-script files
in a public repo
AND SHALL recommend an out-of-band HF-side cleanup
AND SHALL NOT quote the contents of those files.

### Requirement: Empty NVFP4 model card is captured and routed

The verification MUST record the NVFP4 model-card state and route any empty/absent card
to R-04 with a follow-up recommendation, without performing an HF write from this repo.

#### Scenario: Card-gap drift D4 routes R-04

WHEN `docs/session_4/drift_report.md` is read
THEN drift D4 SHALL record the NVFP4 card state
AND SHALL route it to R-04
AND SHALL recommend populating the card as an out-of-repo follow-up.

### Requirement: Risk register and evidence map are updated

The session MUST update `docs/risk_register.md` (at least R-03 and R-04) and
`docs/evidence_map.md` with the verification results and any new drift rows.

#### Scenario: Risk and evidence updates present

WHEN `docs/risk_register.md` and `docs/evidence_map.md` are read
THEN R-03 and R-04 SHALL reflect the Session 4 verification outcome
AND `docs/evidence_map.md` SHALL contain rows recording the FP8/NVFP4 revisions,
license, layout, and drift findings with the verification date.
