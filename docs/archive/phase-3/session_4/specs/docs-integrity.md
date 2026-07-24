# Spec — docs-integrity

Capability refined by UX-S4. Refs FR-9, FR-10, INV-4; eval
`EV-UX-DOCS-LINKS-RESOLVE`. Source: `docs/session_4/design.md` D1/D3.

## ADDED Requirements

### Requirement: Every internal link resolves

Every relative link in `README.md`, `SECURITY.md`, and `CONTRIBUTING.md` SHALL
point at a path that exists in the tracked tree.

#### Scenario: Relative-link resolver runs over the three root docs

- **WHEN** every relative Markdown link and image path in `README.md`,
  `SECURITY.md`, and `CONTRIBUTING.md` is resolved against the repo root
- **THEN** each target exists on disk
- **AND** the resolver reports zero unresolved links.

### Requirement: No dangling or archived references

`README.md` and `SECURITY.md` SHALL NOT reference the archived
`docs/release_checklist.md`, and SHALL NOT carry a live `R-16` reference (R-16 is
a deferred/archived risk; the live phase-3 risk is `R-01`).

#### Scenario: Sweep for archived references

- **WHEN** `rg -n "release_checklist|R-16" README.md SECURITY.md` runs
- **THEN** it returns no matches, or only a reference repointed to a live target
  (e.g. `R-01`), never the archived `docs/release_checklist.md` path or a live
  `R-16` pointer.

### Requirement: No residual auth prose

`README.md` and `SECURITY.md` SHALL NOT contain the removed auth tokens
`COSMOS3_API_KEY` or `X-API-Key` (auth was removed in UX-S1; UX-S4 must not
reintroduce it).

#### Scenario: Sweep for auth tokens

- **WHEN** `rg -n "COSMOS3_API_KEY|X-API-Key" README.md SECURITY.md` runs
- **THEN** it returns no matches.

### Requirement: Slim honest security/status callout

`README.md` SHALL carry exactly one slim "Status & security" section that states
the honest posture, and it SHALL NOT imply that GPU-unverified modes are
verified.

#### Scenario: Reviewer reads the Status & security section

- **WHEN** a reviewer reads the Status & security section
- **THEN** it states there is no application-layer auth, the deployment assumes a
  trusted LAN, ports bind loopback by default (LAN is an explicit opt-in), and
  the API mounts a root-equivalent Docker socket
- **AND** it states the generation stack ships with guardrails off by default
- **AND** its per-mode verification status matches `docs/evidence_map.md`: only
  text→image (FP8/NVFP4) is claimed GPU-verified; other GPU paths are described
  as implemented/CPU-tested behind the manual gate, never as verified.

### Requirement: 720p VRAM advisory is honest

Where `README.md` states the 720p video default, it SHALL note that 720p video is
served by the quantized FP8/NVFP4 path (not the BF16 base) and carry the
thin-FP8-headroom advisory (R-05).

#### Scenario: Reader reads the 720p default claim

- **WHEN** a reader reads the 720p video default statement
- **THEN** it attributes 720p video to the FP8/NVFP4 path and does not claim the
  BF16 base serves 720p video
- **AND** it references the VRAM advisory rather than promising headroom.
