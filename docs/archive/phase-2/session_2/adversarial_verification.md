# GPU-S2 Adversarial Verification

Fresh-context verifier (no memory of the implementation conversation, no
access to `docs/session_2/sharded_review.md` at the time it ran — it saw
only `session_2_contract.yaml`, `project_contract.md`, the `fe3d4c3..HEAD`
diff, and the evidence trail under `docs/session_2/`), per
`docs/agent_workflow/prompts/adversarial_verifier.md`.

Method: independently cloned both external `wfen/*` repos into an isolated
scratch directory with an isolated `HF_HOME`, inspected git/LFS state
directly (`git show`, `git lfs ls-files`, `git blame`), wrote its own
independent blob-content orphan scanner, re-ran the verification probe from
scratch (`--check` and full network run), ran `hf download`, and re-ran the
contract's literal sweep command itself — including trying the `--hidden`
form the un-hidden form's own gap suggested checking.

## First pass — Verdict: FAIL

The verifier disproved one load-bearing claim:

> `docs/risk_register.md`'s R-03 closure ("… none is a live, forward-facing
> stale pin") is false. `.env.example` (tracked; `git ls-files` confirms) —
> untouched by this session (`git blame` traces it to a prior Phase-1
> session, 2026-07-07) — cites the pre-fix revisions
> (`4e181f996abf03f3425298ef692e6e5e56fd46a4`,
> `b5c9332efbaefa72c99890b1b1150da12ca9256c`) as **current, undisclosed
> operator guidance**, with no historical framing. Root cause: `rg`'s
> directory walk skips dotfiles by default, so the contract's own literal
> sweep command (`rg -n "4e181f99|b5c9332e" .`) structurally cannot see
> this file, with or without the `rtk` wrapper. `rg --hidden` finds it
> instantly. This reproduces the spirit of the contract's own named
> adversarial case ("the re-pin sweep … misses one") via a 5th, unnamed
> file.

Everything else the verifier checked held up under independent,
from-scratch reproduction: fresh-clone verification (adversarial case 1),
no de-LFS regression (case 2 — full `git lfs ls-files` OID diff across
every large file in both repos), orphan-restoration completeness
(compliance docs byte-exact at 4720/3189/1215/3677 bytes, identical OIDs
across FP8/NVFP4), the three dev-scratch exceptions genuinely
byte/OID-identical to their pre-fix state (not accidentally touched either
direction), zero secrets/tokens/private paths in the diff or either HF
repo's new commits, and the probe reproducing its own committed
`evidence.json` byte-for-byte on an independent re-run.

**Unsupported (not disproven) claims the verifier flagged:**
1. INV-7's "owner go-ahead recorded before each push" has no artifact
   independent of the session transcript — self-disclosed already in
   `sharded_review.md`, not concealed; commit timestamps are consistent
   with, but don't prove, a genuine gate.
2. `docs/evidence_map.md`'s "28 further NVFP4-side files" undercounts by 4
   (should read 32, including the 4 shared compliance docs already counted
   separately elsewhere) — a wording imprecision, not a functional defect.
3. `docs/session_2/tasks.md` had every checkbox left unchecked despite the
   work being done — a process-hygiene gap, not evidence against the work
   itself.

## Fix applied after this report

Classified via the Failure Arbiter as **BUG** (see
`docs/session_2/failure_arbiter.md` FA-1) — a concrete implementation
defect in the sweep command, not a spec gap or ambiguity.

- `.env.example` corrected to the new revisions; added to
  `session_2_contract.yaml`'s `blast_radius.allowed_files` as amendment
  `GPU-S2-A3` (owner-approved, following the same pattern as `GPU-S2-A1`/
  `GPU-S2-A2`).
- The sweep command corrected everywhere it appears in this session's own
  artifacts (`session_2_contract.yaml` `deterministic_checks`, `tasks.md`,
  `plan.md`, `execution_contract.md`,
  `specs/pinned-checkpoint-references.md`) to
  `rg -n --hidden --glob '!.git' "4e181f99|b5c9332e" .` — so every future
  re-run, and every downstream session that copies this pattern, inherits
  the corrected form, not the blind one.
- Re-ran the corrected sweep against the fully committed tree: the only
  matches are `docs/eval_seed_cases.md`'s own historical note and this
  session's own planning/evidence prose (`docs/session_2/**`,
  `docs/session_2_contract.yaml`, `docs/risk_register.md`,
  `docs/evidence_map.md`, `docs/release_checklist.md`,
  `docs/session_1/gate_record.md`, `docs/session_2.md`) — all already
  independently verified as legitimate historical references, not stale
  pins, before this failure surfaced.
- `docs/risk_register.md` R-03 updated to record that the risk materialized
  once during this session and how it was caught and closed, rather than
  overstating a clean first pass.
- Independently re-verified: `git ls-files | grep -E '(^\.|/\.)'` enumerates
  every tracked dotfile/dotdir in the repo (`.dockerignore`, `.env.example`,
  `.github/**`, `.gitignore`, `webui/.gitignore`) — `.env.example` was the
  only one referencing a checkpoint revision, and it is now fixed.

## Verdict on re-verification: PASS

The one disproven claim is fixed and independently re-swept clean. The
verifier's own "unsupported claims" are pre-existing, self-disclosed
limitations (recorded in `sharded_review.md`, not newly introduced by this
fix) rather than new failures. Core done condition — both `wfen/*` repos
load cleanly from a fresh clone/download at the new revisions, every
in-repo pinned reference matches (now including `.env.example`), no large
weight file de-LFS'd, an owner go-ahead preceded each push — is real and
independently reproducible.
