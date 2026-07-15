# Session 5 Tasks

## 1. Submission Branch Freshness

- [x] 1.1 Fetch `vllm-project/vllm-omni` `main` in the external fork checkout.
- [x] 1.2 Attempt a clean rebase of `gpu-s4-quant-loader-isolation` onto current `upstream/main`.
- [x] 1.3 Record new upstream base, branch head, and conflict or no-conflict outcome.
- [x] 1.4 Run post-rebase diff file-list and forbidden-residue sweeps.
- [x] 1.5 Stop and route back to `GPU-S4` if rebase conflict or semantic drift appears.

## 2. Precheck And Local CI Gate

- [x] 2.1 Run or reconstruct `precheck-pr` quick mode and save the report.
- [x] 2.2 Classify and fix any quick-mode blockers inside `GPU-S5` scope.
- [x] 2.3 Run or reconstruct `precheck-pr` full mode and save the report.
- [x] 2.4 Classify and fix any full-mode blockers or High/Critical findings inside scope.
- [x] 2.5 Run targeted quant pytest set and `python -m compileall vllm_omni`.
- [x] 2.6 Run local `pre-commit` on changed files or all files as practical.
- [x] 2.7 Run local wheel build equivalent where practical.
- [x] 2.8 Record local checks and any ENVIRONMENT limitations.

## 3. DCO, PR Metadata, And Owner Gate

- [x] 3.1 Verify every PR commit includes a `Signed-off-by` trailer.
- [x] 3.2 Determine PR type and title prefix from upstream guidance and precheck results.
- [x] 3.3 Draft PR title and body.
- [x] 3.4 Push the final branch state to `fengwang/vllm-omni`.
- [x] 3.5 Stop and request explicit owner go-ahead immediately before `gh pr create`.
- [x] 3.6 If approved, open the PR against `vllm-project/vllm-omni` `main`.
- [x] 3.7 Run `gh pr checks <PR>` and record status.

## 4. Review, Verification, And Closeout

- [x] 4.1 Run sharded review over correctness, security/safety, tests, architecture, and performance.
- [x] 4.2 Fix only Critical/High review findings and re-check.
- [x] 4.3 Run adversarial verification against the session contract, diff, and evidence.
- [x] 4.4 Run final deterministic checks listed in the session contract.
- [x] 4.5 Update `docs/evidence_map.md`, `docs/risk_register.md`, and `docs/eval_seed_cases.md`.
- [x] 4.6 Update `docs/handoff.md` with PR URL or non-submission reason.
- [x] 4.7 Verify `GATE-GPU-S5-PR` done condition and record remaining risks.
