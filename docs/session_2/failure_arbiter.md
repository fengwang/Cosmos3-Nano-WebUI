# GPU-S2 Failure Arbiter

Per `docs/agent_workflow/prompts/failure_arbiter.md` / `AGENTS.md`
Verification: classify before fixing.

## FA-1 — Re-pin sweep missed `.env.example` (dotfile blind spot)

- **Classification: BUG.** The implementation violated a clear contract
  clause (`session_2_contract.yaml` acceptance_criteria: "No stale pin
  remains anywhere in the repository, confirmed by a whole-repository
  sweep"; `project_contract.md` Hard Commitment 3 / INV-5). This is not a
  SPEC_GAP (the contract's intent was unambiguous — sweep the *whole*
  repository) or an AMBIGUITY (there was one correct reading). It is a
  concrete implementation defect: the literal sweep command
  (`rg -n "4e181f99|b5c9332e" .`) silently skips dotfiles by default, so it
  never scanned `.env.example`, which cited the pre-fix revisions as live,
  undisclosed operator guidance.
- **How it was caught:** not by this session's own sweep or sharded
  review — both ran the same blind command. Caught by the fresh-context
  adversarial verifier (`docs/session_2/adversarial_verification.md`),
  which independently re-ran the check with `--hidden` specifically because
  it was instructed to reproduce claims from scratch rather than trust the
  record.
- **Fix:** `.env.example` corrected to the new revisions (amendment
  `GPU-S2-A3`, added to `blast_radius.allowed_files`); the sweep command
  itself corrected everywhere it's documented in this session
  (`session_2_contract.yaml`'s `deterministic_checks`, `tasks.md`,
  `plan.md`, `execution_contract.md`, `specs/pinned-checkpoint-references.md`)
  to require `--hidden --glob '!.git'`. Regression test: the corrected
  sweep command is now the one every future re-run and every downstream
  session inherits from this contract, not the blind one.
- **Repeat check:** this is the first and only occurrence of this specific
  failure in this session — did not repeat, so no second-strike escalation
  was needed.

## No other Critical/High failures required classification this session

The sharded review's F1/F2/F3 (probe logic gaps, stale spec text) were
caught and fixed inline during the review pass itself, before an
adversarial verifier ran — classified informally as BUG (probe logic) and
BUG (stale doc) respectively in `docs/session_2/sharded_review.md`'s
Disposition section, not escalated here since they didn't recur after the
first fix attempt.
