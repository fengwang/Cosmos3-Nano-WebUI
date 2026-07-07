# Session 8 Execution Contract - Release Gate, Evidence Review, and Handoff

Session: MIG-S8
Risk: high · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S8-BETA`

## Planned file changes

Created:
- `docs/session_8/{brainstorming,proposal,design,tasks,plan,execution_contract}.md`
- `docs/session_8/specs/{deterministic-checks,acceptance-matrix,evidence-review,gate-record,
  gpu-beta-limited-disposition,doc-reconciliation}.md`
- `docs/session_8/outputs/{acceptance_matrix,deterministic_checks,evidence_review,
  gate_record}.md`
- `docs/session_8/{failure_arbiter (if any),sharded_review,adversarial_verification}.md`
- `docs/eval_corpus/mig_s8_*.md`

Modified:
- `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
  `docs/handoff.md`, `docs/release_checklist.md`

## Allowed blast radius

Permitted (contract `blast_radius.allowed_files`): `docs/session_8/**`,
`docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
`docs/handoff.md`, `docs/release_checklist.md`. Running (not editing)
`tests/test_private_ref_scan.py` and the read-only/render-only deterministic checks is
in-bounds.

Forbidden (stop and surface to the owner if a change seems required): runtime source
(`api/**`, `webui/**`) except an owner-approved release fix; model-weight/media files;
`schemas/openapi.json`; `pyproject.toml`/`uv.lock`/`package.json` pins (`INV-10`); Docker
publishing workflows; vLLM-Omni fork source. No new feature work; no lowering an acceptance
bar without an owner decision; no push/tag/release; no private-evidence citation.

## First test to write

The release gate's first assertion is that the CPU deterministic checks still pass on the
current tree (they are the evidence of record). Before writing any output doc:

```bash
uv sync --frozen --group test-cpu && uv run pytest -m "not gpu" -q   # expect: pass (≈485)
uv run python tests/test_private_ref_scan.py                          # expect: 0 findings
```

The first *documentation* assertion (acceptance-matrix spec): every MUST-keyword requirement
in `docs/prd.md` §4 maps to exactly one matrix row. A matrix missing any PRD MUST FAILS this
assertion.

## Checks to run after each task

- **Checks task:** the 7 contract deterministic checks (`rtk git status`; `pytest -m "not
  gpu"`; webui `build`/`lint`/`typecheck`/`test`; private-ref scan; weight/media scan;
  `docker compose config` fp8 + nvfp4). Record raw output; classify any failure first.
- **Outputs tasks:** each output doc self-tested against its spec scenarios — acceptance
  matrix covers every PRD MUST and every `PASS` cites public evidence; evidence review is
  scanner-clean and every row tagged verified/deferred; gate record has all 8 gates + the
  recommended verdict.
- **Reconciliation task:** `tests/test_private_ref_scan.py` clean over the edited docs; risk
  register has no unowned release-blocking risk; no cross-doc contradiction with the README
  claim matrix / `docs/model_setup.md`.
- **After any doc edit:** re-run the private-reference scan over `docs/session_8/**` and the
  edited tracking docs.

## Review axes to run at the end

correctness · security · tests · architecture · performance (per
`docs/agent_workflow/prompts/sharded_review.md`), re-aimed at the release *claims*: does the
acceptance matrix cover every MUST; does any `PASS`/`GO` rest on absent or private evidence;
is any GPU/deferred surface presented as verified; is any release-blocking risk unowned; do
the reconciled docs contradict the README/Docker/setup. Each reviewer is read-only and
reports severity + file/line evidence + violated clause/invariant + smallest safe fix +
confidence. **Reviewer output is untrusted** — reject any axis returned with 0 tool uses or
no evidence and re-run it. Fix only High/Critical; re-run checks after fixes.

## Adversarial verifier brief

Fresh context; sees only `docs/session_8_contract.yaml`, `docs/project_contract.md`, the
session diff, and the evidence outputs — not this conversation. Task: falsify
"`GATE-MIG-S8-BETA` can record an evidence-based GO recommendation with risks and
limitations reconciled." Attempt the contract's adversarial cases: (a) a gate/matrix row
accepts a claim with no public evidence; (b) the GPU disposition is recorded as run, or omits
the pin/revisions a later run must match; (c) the private-reference scan is scoped too
narrowly (miss `docs/session_8/**` or a tracking-doc edit); (d) a release-blocking risk is
left open without an owner decision; plus the failure modes: (e) a reconciled doc contradicts
the README or Docker setup; (f) a GPU-skipped surface reads as supported; (g) CPU-CI-green is
presented without the GitHub-runner-unverified qualifier. Any confirmed item fails the
session and routes through the Failure Arbiter.

## Concrete done condition

`GATE-MIG-S8-BETA` is ready for owner ratification when all hold, each backed by evidence:
1. `deterministic_checks.md` records the 7 CPU checks re-run with raw results, and every
   check that could not run is recorded with a reason.
2. `acceptance_matrix.md` has one row per PRD MUST (FR-1..12 where MUST, NFR-1..6) → gate →
   public evidence → verdict; FR-9 and NFR-6 are `BETA-LIMITED` with the deferred command;
   no `PASS` rests on private evidence.
3. `evidence_review.md` ties each major public claim to a public evidence row and separates
   verified-now from manual-gate-deferred, with no private citation.
4. `gate_record.md` records `GATE-MIG-S1..S8`, the GPU manual-gate status + pin/revisions,
   drift D1 as a beta limitation, and a recommended `GATE-MIG-S8-BETA` verdict + rule marked
   "owner ratifies".
5. `evidence_map.md`, `risk_register.md`, `eval_seed_cases.md`, and `release_checklist.md`
   are reconciled: no unowned release-blocking risk, GPU cases are the S8 manual gate, and no
   cross-doc contradiction.
6. The private-reference scan is clean over `docs/session_8/**` and the edited tracking docs.
7. Sharded review has no unresolved High/Critical; the adversarial verifier passes (or every
   FAIL is classified and dispositioned).
8. `docs/handoff.md` hands the next session the GPU manual gates (commands + pin/revisions),
   the at-publish tasks, the remaining risks (D1, R-16), and the recommended verdict for
   owner ratification.
