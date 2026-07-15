# Capability: pinned-checkpoint-references

Source: `docs/session_2/proposal.md` (Modified Capabilities)

## MODIFIED Requirements

### Requirement: Every In-Repo Reference Matches The Current Checkpoint Revision
Every tracked file in this repository that cites the FP8 or NVFP4 checkpoint
revision MUST cite the current, post-`GPU-S2` revision — never the pre-fix
`4e181f996abf03f3425298ef692e6e5e56fd46a4` (FP8) or
`b5c9332efbaefa72c99890b1b1150da12ca9256c` (NVFP4) SHA — except inside one
explicitly historical note. This supersedes the pre-`GPU-S2` state, where
these were the current pins.

#### Scenario: model_setup.md cites the new FP8 and NVFP4 revisions
WHEN `docs/model_setup.md` §1's checkpoint table is read after this session
THEN the FP8 row's "Pinned revision" is the new post-fix SHA
AND the NVFP4 row's "Pinned revision" is the new post-fix SHA
AND neither pre-fix SHA appears anywhere in the file.

#### Scenario: evidence_map.md, release_checklist.md, and eval_seed_cases.md agree
WHEN `docs/evidence_map.md`, `docs/release_checklist.md` §7, and
`docs/eval_seed_cases.md` are read after this session
THEN every checkpoint-revision citation in each file matches the same new
FP8 SHA and the same new NVFP4 SHA used in `docs/model_setup.md` §1
AND neither pre-fix SHA appears in any of the three files, except inside the
one explicitly historical note permitted below.

#### Scenario: risk_register.md and handoff.md are current
WHEN `docs/risk_register.md` (R-02/R-03/R-04 rows) and `docs/handoff.md` are
read after this session
THEN they describe the checkpoint fix as closed with the new revisions, not
as still-open blueprint-time rows citing the pre-fix SHAs.

### Requirement: Whole-Repository Sweep Confirms No Stale Survivor
Closing this session MUST include a whole-repository text search for both
pre-fix revision SHAs (by an 8-character prefix, to also catch abbreviated
citations) across every tracked file, not only the four files named as the
minimum floor. Any match outside the one documented historical exception is
a hard failure, not a note.

#### Scenario: Sweep finds only the one documented historical exception
WHEN `rg -n --hidden --glob '!.git' "4e181f99|b5c9332e" .` (`--hidden` is
required — the un-hidden form silently skips dotfiles, including
`.env.example`; amendment `GPU-S2-A3`) is run from the repository root after
all re-pin edits are made
THEN the only match outside `docs/archive/phase-1/**` (never edited) and
this session's own planning/evidence prose is `docs/eval_seed_cases.md`'s
own "replacing the pre-fix …" historical reference under "Public Checkpoint
IDs"
AND every other match, if any, is treated as a stale pin requiring another
edit pass before the session closes.

### Requirement: The One Permitted Historical Reference Is Preserved, Not Deleted
`docs/eval_seed_cases.md`'s existing note that the new revision is "replacing
the pre-fix `4e181f996abf03f3425298ef692e6e5e56fd46a4`" (and the equivalent
NVFP4 note) MUST remain, worded as history, rather than being deleted to
make the sweep pass trivially.

#### Scenario: Historical note still names the pre-fix SHA as history
WHEN `docs/eval_seed_cases.md`'s "Public Checkpoint IDs" section is read
after this session
THEN it still states that the current revision replaces the named pre-fix
SHA for both FP8 and NVFP4
AND the wording frames the pre-fix SHA as superseded history, not as a
current or ambiguous pin.
