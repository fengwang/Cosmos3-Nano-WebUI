# Specification - Evidence Review

Session: MIG-S8
Capability: evidence-review

## ADDED Requirements

### Requirement: Major public claims are tied to public evidence

`docs/session_8/outputs/evidence_review.md` MUST tie each major public-facing claim (repo
scrub, vLLM-Omni pin, HF checkpoint metadata/revisions/license, CPU CI, Docker/Compose
render, README/hygiene, license separation) to a public evidence row: a command output, a
tracked repo file, or a public remote / model page. It MUST NOT cite any private source
path, private host, private codename, or private repository.

#### Scenario: Review is public-only

WHEN `tests/test_private_ref_scan.py` runs over the tree including `docs/session_8/**`
THEN it SHALL report 0 findings, and the evidence review SHALL contain no private citation.

#### Scenario: Every reviewed claim has a pointer

WHEN a claim row is read
THEN it SHALL carry a public evidence pointer (command, tracked path, or public URL), or be
explicitly marked speculative / deferred.

### Requirement: Verified-now is separated from manual-gate-deferred

Each claim MUST be tagged as either verified now (CPU checks, scans, render, links, license,
hygiene) or manual-gate-deferred (GPU inference, drift D1, GitHub-hosted CI run, and the
at-publish self-referential links). A deferred claim MUST NOT be presented as a shipped
runtime capability.

#### Scenario: GPU claims are tagged deferred

WHEN a claim about GPU inference, FP8/NVFP4 generation, reasoning, or action is read
THEN it SHALL be tagged manual-gate-deferred and pointed at the `MIG-S8` GPU gate, not
presented as verified runtime behavior.

#### Scenario: CPU-CI-green is qualified

WHEN the CI claim is read
THEN it SHALL state that the checks pass locally and that the GitHub-hosted run is an
at-publish confirmation (nothing pushed).
