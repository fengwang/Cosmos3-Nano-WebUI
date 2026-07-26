# Spec — `walkthrough-per-mode`

Capability: `docs/walkthrough.md` — teach each mode by example with fillable placeholders and no
committed binary. Backed by `EV-AM-WALKTHROUGH-STRUCTURE` (INV-1, R-13, NFR-1).

## ADDED Requirements

### Requirement: Per-mode example input → expected output
`docs/walkthrough.md` SHALL contain a section for each verified mode — Studio (with the t2i worked
example and the video sub-modes), Reasoning, and Action — and each SHALL give a concrete example input,
the UI action to run it, and the expected output. Expected-output prose SHALL match a real,
owner-approved run (R-13); example *inputs* MAY be drafted where a recorded prompt is unavailable, but
expected *outputs* SHALL NOT be invented.

#### Scenario: Every verified mode is present with input + expected output
- WHEN `docs/walkthrough.md` is read
- THEN it has a Studio section (t2i example: "a red apple on a wooden table, studio photo", 480×480 →
  a clean studio-style image), a Reasoning section (a recorded prompt → its recorded coherent answer),
  and an Action section (forward_dynamics: Embodiment `agibotworld` + Mode `Forward dynamics` → Run demo
  → a rollout video + 3D robot view), each with an explicit "expected" description.

#### Scenario: Expected outputs trace to recorded runs
- WHEN each expected-output line is checked against `docs/session_{2,3,4,5}/evidence/*` or the owner
  attestation in `docs/evidence_map.md`
- THEN each has a traceable source (no output asserted for a mode/format that never ran on GPU).

### Requirement: Image placeholders under `docs/images/`, no committed binary
Every image reference in `docs/walkthrough.md` SHALL be a markdown link of the form
`![...](docs/images/<mode>-<example>.png)` under `docs/images/`, and NO image or media binary SHALL be
committed by this session (INV-1); the owner populates the images later.

#### Scenario: Every image link is a placeholder under docs/images/
- WHEN `rg -n "docs/images/" docs/walkthrough.md` runs
- THEN every image embed points under `docs/images/` and matches `<mode>-<example>.png`; there is at
  least one placeholder per verified mode.

#### Scenario: No image binary is committed (negative control)
- WHEN `git status --porcelain docs/images` runs after the edits
- THEN it prints nothing (no `docs/images/*` binary added, staged, or committed).

### Requirement: UI-first, ADHD posture, reproducible-via-API pointer
`docs/walkthrough.md` SHALL be UI-first (open the tab → do the UI action → observe), carry a shared
"Setup once" preamble, use ADHD structure (TL;DR, in-page anchors, fenced commands with language IDs,
`<details>` for verbose API detail with a blank line after `</summary>`), and point to the exact API
request bodies in `docs/session_3/action_demo_runbook.md` / `docs/model_setup.md` rather than re-inlining
them.

#### Scenario: ADHD structure present
- WHEN `docs/walkthrough.md` is read
- THEN it contains a TL;DR near the top, a "Jump to" / anchors block, at least one `<details>` whose
  `</summary>` is followed by a blank line, and all shell commands are in fenced blocks with a language id.

#### Scenario: Setup preamble brings up a stack before any mode
- WHEN the "Setup once" section is read
- THEN it shows `make up-fp8` (or `make up-nvfp4`), `make health`, and opening `http://localhost:3000`,
  and references no BF16 base / `make up-fp8-reasoning` overlay (zero-BF16).
