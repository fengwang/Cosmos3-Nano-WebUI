# Session 2 Tasks - vLLM-Omni Patch Rebase And Public Pin

Date: 2026-07-06
Session: MIG-S2

## 1. Planning And Baseline

- [x] 1.1 Write Session 2 brainstorming, proposal, design, specs, tasks, plan, execution contract, and baseline failure classifications.
- [x] 1.2 Confirm public fork base, local fork cleanliness, selected source range, and remote branch/tag name availability.
- [x] 1.3 Create or refresh the isolated fork test environment `.venv-mig-s2`.

## 2. Public Fork Branch Preparation

- [x] 2.1 Create branch `mig-s2-cosmos3-quant-pin` from public fork `origin/main`.
- [x] 2.2 Record the branch base commit and patch commit list.
- [x] 2.3 Identify the first spec-derived failing or missing test from the selected patch line.

## 3. Patch Replay And Conflict Resolution

- [x] 3.1 Replay ModelOpt-native FP8 adapter commits and resolve conflicts only in allowed adapter/test surfaces.
- [x] 3.2 Replay NVFP4 runtime commits and resolve conflicts only in allowed Cosmos3, quantization, adapter, and test surfaces.
- [x] 3.3 Replay FP8 W8A16 runtime commits and resolve conflicts only in allowed Cosmos3, quantization, adapter, and test surfaces.
- [x] 3.4 Verify the final fork diff stays within the approved external blast radius.

## 4. Deterministic Checks

- [x] 4.1 Run compile checks from the fork checkout.
- [x] 4.2 Run targeted adapter, quantization, and Cosmos3 guard tests from the fork checkout.
- [x] 4.3 Classify any failing or unavailable checks before fixing source or tests.
- [x] 4.4 Re-run targeted checks after concrete fixes.

## 5. Public Pin Publication

- [x] 5.1 Push public branch `mig-s2-cosmos3-quant-pin`.
- [x] 5.2 Create and push tag `cosmos3-nano-webui-mig-s2`.
- [x] 5.3 Verify branch and tag with `git ls-remote`.
- [x] 5.4 Record the exact pip install command for `MIG-S6`.

## 6. Review, Verification, And Handoff

- [x] 6.1 Run sharded review over correctness, security/safety, tests, architecture, and performance.
- [x] 6.2 Fix only High/Critical findings with concrete evidence, then re-check.
- [x] 6.3 Run adversarial verification against the contract, diff, and evidence.
- [x] 6.4 Update `docs/evidence_map.md`, `docs/risk_register.md`, handoff, and eval seeds if required.
- [x] 6.5 Verify `GATE-MIG-S2-VLLM` done condition.
