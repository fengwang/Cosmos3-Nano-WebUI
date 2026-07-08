# Session 8 - Release Gate, Evidence Review, and Handoff

Contract: `docs/session_8_contract.yaml`
Risk: high
Routing: worker_plus_reviewers

## Objective

Review every migration gate, reconcile evidence and risks, run final CPU checks,
record manual GPU gate results, and produce the public beta GO/NO-GO handoff.

## Why This Session Exists

The migration touches public source, dependency pins, model setup, CI, Docker,
README claims, and release hygiene. A final adversarial review is needed before
calling the GitHub repo ready for public beta.

## In Scope

1. Verify `GATE-MIG-S1-SCOPE` through `GATE-MIG-S7-PUBLIC`.
2. Re-run CPU deterministic checks.
3. Review private-reference scans, model-weight scans, and Docker render checks.
4. Review HF checkpoint evidence and vLLM-Omni pin.
5. Run or review manual GPU gate evidence for all target modes.
6. Reconcile `docs/evidence_map.md`, `docs/risk_register.md`, and
   `docs/eval_seed_cases.md`.
7. Produce a release handoff with GO/NO-GO, checks run, checks not run, and known
   limitations.

## Out of Scope

- No new feature work.
- No lowering acceptance bars without owner decision.
- No Docker image publishing.
- No private evidence citations.

## Deliverables

- `docs/session_8/outputs/acceptance_matrix.md`
- `docs/session_8/outputs/deterministic_checks.md`
- `docs/session_8/outputs/evidence_review.md`
- `docs/session_8/outputs/gate_record.md`
- Final updates to evidence, risk, and eval docs.
- Public beta handoff.

## Deterministic Checks

```bash
rtk git status --short --branch
rtk pytest -q
rtk proxy sh -lc 'cd webui && pnpm lint && pnpm typecheck && pnpm test'
rtk rg -n "$PRIVATE_REF_PATTERN" .
rtk rg -n "\\.(safetensors|pt|pth|ckpt|mp4|mov|avi)$" .
rtk docker compose -f deploy/docker-compose.fp8.yml config
rtk docker compose -f deploy/docker-compose.nvfp4.yml config
```

Record checks that cannot run because their files are not part of the final
public scope.

## Exit Criteria

- `GATE-MIG-S8-BETA` records owner GO or NO-GO.
- Every PRD MUST is passed, explicitly marked beta-limited, or routed to a
  follow-up risk.
- Public claims match evidence.
- Checks run and checks not run are recorded.

## Handoff

Record final commits, vLLM-Omni pin, HF checkpoint revisions, CI workflow names,
Docker commands, manual GPU results, known limitations, and the recommended next
development session.
