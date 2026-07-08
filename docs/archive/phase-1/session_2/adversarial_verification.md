# Session 2 Adversarial Verification

Date: 2026-07-06
Session: MIG-S2
Inputs: session contract, project contract, fork diff, check outputs, evidence

## Disproven Claims

None.

## Unsupported Claims

- A clean Docker build or clean `pip install` from the public tag is not proven
  in Session 2. This is not claimed as complete; it remains a `MIG-S6` gate.
- GPU runtime, VRAM, throughput, and checkpoint artifact compatibility are not
  proven in Session 2. They remain `MIG-S4` and `MIG-S8` gates.

## Strongest Counterexample

The exact YAML-listed pytest command still references
`tests/diffusion/quantization/test_nvfp4_blockwise_config.py`, which does not
exist in the rebased patch. Running the exact command exits with pytest code 4:

```text
ERROR: file or directory not found: tests/diffusion/quantization/test_nvfp4_blockwise_config.py
```

Disposition: PASS with classification. The failure is already classified as
AMBIGUITY because `docs/session_2.md` states exact test paths may change with the
fork, and the preserved patch path is
`tests/model_executor/quantization/test_nvfp4_blockwise_config.py`. The expanded
targeted suite using the actual path passed with `118 passed, 22 warnings`.

## Acceptance Criteria Check

- Public vLLM-Omni pin exists: PASS. Remote branch and tag both resolve to
  `697035018b70cef76b974a909d23371a9984c3f2`.
- Selected patch line present: PASS. Fork branch contains the eight selected
  patch commits plus one review-fix commit.
- Deterministic checks: PASS with accepted classification for the stale path.
  Compileall passed; expanded targeted pytest passed.
- Install command recorded: PASS. `docs/handoff.md` records the tag-based public
  install command.
- Evidence/risk docs updated: PASS. `docs/evidence_map.md` and
  `docs/risk_register.md` include the final pin disposition.
- Review artifacts saved: PASS. `docs/session_2/sharded_review.md` and this file
  exist.

## Invariant Check

- WebUI repo consumes only a public vLLM-Omni commit or tag: PASS.
- Fork pin is reproducible from public GitHub state: PASS via `git ls-remote`.
- Test failures classified before source changes expanded: PASS. Environment,
  ambiguity, and review-found BUG cases are recorded in
  `docs/session_2/failure_arbiter.md`.
- Public docs contain no known private source path or private source hash leaks:
  PASS by targeted scrub scan.

## Blast Radius Check

External fork changes are limited to checkpoint adapters, diffusers loader,
Cosmos3 load hooks, quantization config surfaces, and matching tests. WebUI repo
changes are docs-only: `docs/session_2/**`, evidence/risk docs, handoff, and eval
seeds required by the lifecycle.

## Verdict

PASS. `GATE-MIG-S2-VLLM` is satisfied with residual risks deferred to their
planned sessions.
