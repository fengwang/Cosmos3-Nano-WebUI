# Specification - Public Fork Patch Pin

Session: MIG-S2
Capability: Public Fork Patch Pin

## ADDED Requirements

### Requirement: Public branch contains the selected patch line

The vLLM-Omni GitHub fork SHALL contain a public branch named
`mig-s2-cosmos3-quant-pin` whose history includes the selected Cosmos3 patch line
rebased or cherry-picked onto the public fork base.

#### Scenario: Branch is visible on the public fork

WHEN `git ls-remote git@github.com:fengwang/vllm-omni.git refs/heads/mig-s2-cosmos3-quant-pin` is run
THEN it SHALL return a commit hash for the public branch
AND the commit SHALL be reachable from the local rebased branch.

### Requirement: Immutable tag pins the dependency

The vLLM-Omni GitHub fork SHALL contain tag `cosmos3-nano-webui-mig-s2` pointing
to the final accepted commit. Later WebUI install instructions MUST use the tag
or commit hash, not the branch name alone.

#### Scenario: Tag resolves publicly

WHEN `git ls-remote git@github.com:fengwang/vllm-omni.git refs/tags/cosmos3-nano-webui-mig-s2` is run
THEN it SHALL return the same final commit recorded in Session 2 evidence
AND the install command SHALL reference the tag or commit hash.

### Requirement: Public-safe patch provenance is recorded

Session 2 SHALL record the target base commit, owner-authorized eight-commit
source range descriptor, final public commit, and any conflict resolutions. It
MUST NOT record private source paths, private branch names, or private source
hashes in public docs.

#### Scenario: Handoff includes pin provenance

WHEN `docs/handoff.md` is read after Session 2
THEN it SHALL include the public branch, tag, commit hash, install command, and
known caveats for `MIG-S3`, `MIG-S4`, and `MIG-S6`
AND it SHALL describe source provenance only in public-safe terms.
