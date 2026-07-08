# GPU-S1 Adversarial Verification

Fresh-context verifier (no memory of the implementation conversation),
given only `docs/session_1_contract.yaml`, `docs/project_contract.md`, the
`phase-2...GPU-S1` diff, and the evidence trail under `docs/session_1/`, per
`docs/agent_workflow/prompts/adversarial_verifier.md`.

Method: independently reproduced the load-bearing claims from scratch rather
than trusting the record — recomputed Docker layer-set intersections,
re-ran the sm_120 matmul probe, re-triggered both the guardrails-on crash
and the guardrails-off success live, re-hashed and visually inspected both
T2I PNGs, hit the GitHub API to confirm the pinned SHA, and diffed every
changed file against the blast radius.

## Disproven claims

None. Every load-bearing claim attempted was independently reproduced and
held up (sm_120 support, zero cosmos3-layer reuse beyond shared base
ancestry, no baked weights, immutable SHA pin, both guardrails behaviors,
both T2I artifacts' hashes and content, `docker-compose.local-image.yml`
absence, full blast-radius compliance including the GPU-S1-A1 amendment).

## Unsupported claims

1. GPU-S1-A1's approval trail (a YAML comment + commit message) is thinner
   than the original scope's verbatim-quoted approval — plausible given
   this repo's existing convention, not independently verifiable further.
2. `gate_record.md`'s Step 2 layer count was arithmetically off by one (35
   vs. the correct 36 = 34 base + 2 new `RUN` layers) — the substantive
   conclusion (zero overlap with the new layers) was unaffected. **Fixed**
   in `gate_record.md` following this report.
3. F6 ("behaviorally equivalent" `/v1/models` claim) — already self-flagged
   in `sharded_review.md`; remains open by design (Medium, not fixed this
   session).

## Strongest counterexample

The contract's literal `deterministic_checks` do not pass for the built
image as written — confirmed by direct reproduction, not just by re-reading
the implementer's own disclosure. Assessed as already honestly surfaced
(via `gate_record.md`'s dedicated re-run section, `evidence_map.md`,
`release_checklist.md`, and `sharded_review.md` F2/F6) rather than
concealed, and as the correct behavior for a high-risk gated session to
produce, not a failure of it.

## Verdict: PASS

Core done condition (public, from-source `deploy/vllm-omni.Dockerfile`
building clean and serving verified T2I on the RTX 5090 for both FP8 and
NVFP4) is real and independently reproducible. All 4 named
`adversarial_cases` are genuinely ruled out. INV-1/INV-2/INV-3 hold under
direct inspection. Blast radius respected.

## Follow-up applied after this report

- `gate_record.md` layer-count corrected (35 → 36).
- `risk_register.md` gained a new row (R-10) tracking the guardrails-on
  generation path as unverified pending gated-model/`HF_TOKEN`
  provisioning, closing the loop `sharded_review.md` F2 left open.
