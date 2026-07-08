# Session 1 Brainstorming

Date: 2026-07-06
Session: MIG-S1

## Context Read

- `docs/prd.md` defines a documentation-first public beta migration.
- `docs/session_1.md` limits this session to public repo inventory and migration scope.
- `docs/session_1_contract.yaml` sets risk to low and allows changes under `docs/session_1/**`, `docs/evidence_map.md`, `docs/risk_register.md`, and `docs/eval_seed_cases.md`.
- The user explicitly amended the blast radius to allow `docs/handoff.md` for the session end protocol.
- `docs/project_contract.md` requires public evidence only, no model weights, no generated media, no private paths, no source import, and no public product surface changes in this session.
- `docs/evidence_map.md` and `docs/risk_register.md` already contain blueprint-time evidence and risk rows.
- No `docs/handoff.md` existed at startup.

## Startup Evidence

- Branch: `session-1`.
- Clean status at startup: `git status --short` returned no entries.
- HEAD at startup: `76e60a26e73dde0a0e39287d55fe2ce47e2e0ba4`.
- Recent commits:
  - `76e60a2 ignore session related documents`
  - `bc8ecc7 blueprint created`
  - `d1b6e84 prepare for migration`
  - `c3983f7 origin/main initialize repo`
- Public WebUI remote: `git@github.com:fengwang/Cosmos3-Nano-WebUI.git`.
- Public WebUI remote HEAD/main: `c3983f7fc68c3718e870dfcbab0f0141a1566764`.
- Public vLLM-Omni remote HEAD/main: `d4a869fe5e2edd49af48026051948c8d1018d727`.
- Current file tree contains blueprint docs, `README.md`, and `misc/logo.png`.
- `README.md` is empty.
- `misc/logo.png` is present.

## Clarifications

1. `docs/handoff.md` is allowed for this session because the user selected option `a`: treat the Session End Protocol as a blast-radius amendment.
2. Session 1 operational deliverables will be separate files under `docs/session_1/`: `inventory.md`, `import_manifest.md`, `exclusion_manifest.md`, and `scrub_checklist.md`.
3. Commits are expected after each completed task checkpoint because the user selected option `b`.

## Approaches Considered

### Approach A: Contract Pack Plus Operator Artifacts

Create lifecycle files under `docs/session_1/`, then implement separate operator-facing deliverables:

- `inventory.md`
- `import_manifest.md`
- `exclusion_manifest.md`
- `scrub_checklist.md`

This gives later sessions direct inputs without making them extract rules from a narrative document. The trade-off is a larger file count.

### Approach B: Lifecycle First, Artifacts Second

Write proposal, design, specs, tasks, plan, and execution contract first, then derive operational artifacts afterward. This gives strong process traceability but delays the concrete deliverables and risks duplicate wording.

### Approach C: Single Narrative Scope File

Write one comprehensive scope document. This is concise, but it weakens the handoff to `MIG-S2` and `MIG-S3` because future workers must find import, exclusion, and scrub rules inside prose.

## Chosen Approach

Approach A is approved.

It matches the user-selected file layout, the low-risk Session 1 contract, and the handoff needs for `MIG-S2` and `MIG-S3`.

## Validated Design

### Scope And Artifacts

The session will create lifecycle planning files and four operational artifacts. The operational artifacts have clear responsibilities:

- Inventory records observed public repo state and command evidence.
- Import manifest lists allowed future import categories and required proof.
- Exclusion manifest lists material excluded by default.
- Scrub checklist defines repeatable scans and fallback patterns.

### Data Flow

Using functional thinking:

- Data: branch name, commit IDs, remote URLs, file list, allowed import categories, excluded path classes, scrub patterns, check outputs.
- Calculations: classification of files into include or exclude categories, interpretation of scan results, evidence drift decisions.
- Actions: running `git`, `rg`, and remote probes; writing docs; committing checkpoints.

The impure shell is limited to deterministic command runs and file writes. The decisions are recorded as data so later sessions can reuse them without re-running private context.

### Concept Boundaries

Using concept design at documentation scale:

- `PublicRepoInventory` owns the purpose of recording what exists now.
- `MigrationScopePolicy` owns what future sessions may import or must exclude.
- `PrivateReferenceScrubbing` owns private-reference and artifact scan rules.
- `EvidenceHandoff` owns how baseline drift and next-session warnings are passed forward.

These concepts are documented separately rather than merged into one broad scope note.

### Checks

Each task uses deterministic shell checks derived from specs:

- File existence checks for required artifacts.
- Heading and content checks with `rg`.
- Scrub scans for private references and model or media artifacts.
- Git blast-radius checks before commits.
- Contract baseline checks from `docs/session_1_contract.yaml`.

### Risks

- The exact contract scrub command depends on `$PRIVATE_REF_PATTERN`, which is unset in the current shell. This is classified as an environment/setup gap. The session will define a fallback pattern and record the issue.
- The existing evidence map contains historical blueprint-time rows. Session 1 will not rewrite history, but it will add or adjust rows if the current public baseline has drifted.
- Scope creep into source import, Docker, README rewrite, vLLM-Omni rebase, or checkpoint validation is explicitly out of scope.

## Approval

The user approved the artifact design and instructed the session to proceed.
