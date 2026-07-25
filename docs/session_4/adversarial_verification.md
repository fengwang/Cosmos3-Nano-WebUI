# AM-S4 Adversarial Verification

Date: 2026-07-25. Protocol: `docs/agent_workflow/prompts/adversarial_verifier.md`. A fresh-context
verifier that did NOT write the code or participate in the review, given ONLY the session contract,
project contract, the git diff, and the `docs/session_4/**` evidence — **not** the implementation
conversation. Its job: falsify "GATE-AM-S4-ORCHESTRATION is satisfied".

Scope note: this pass ran on the **orchestration** diff (cold-start + legacy-BF16 deletion + coresidency
+ wiring tests + docs), before the owner-reported reasoning-400 fix. That fix is separately evidenced in
`evidence/P2-reasoning-400-fix.md` with its own reproduction + regression guard.

## Verdict: PASS (could not falsify the technical done condition)

The verifier re-ran every deterministic check itself (did not trust claims): CPU suite exit 0; fp8
`config` all-modes with **0 BF16 mounts** both raw and `--env-file .env`; `rg` legacy sweep clean;
`schemas/openapi.json` unchanged; `tests/deploy` green. It disproved all nine attack angles:

1. **BF16 survives the default path (INV-4)** — disproved. Even with the owner's stale untracked `.env`
   (which still sets `COSMOS3_BASE_DIR` etc.), the rendered config is BF16-free — no compose file
   references those vars after the overlay deletion.
2. **Boot co-load race** — disproved. `up -d --no-start` → `stop` heavy → `start api webui`; the only
   `depends_on` is webui→api; the explicit stop guard forces both heavy planes down; the single-slot FSM
   (evict-before-load under a lock) is the runtime backstop, so INV-5 does not depend on sample timing.
3. **t2i merely asserted (INV-2)** — disproved. The GPU-smoke artifacts match P1 exactly: `smoke_t2i.png`
   and the post-swap `smoke_t2i_2.png` are **both 691,968 bytes** (byte-identical across the reasoning
   swap); the action MP4 is a valid ftyp; the reason SSE is coherent.
4. **Tests are tautological** — disproved by **mutation**: in an isolated mirror the verifier reintroduced
   each hazard (BF16 `/models/base` mount; a `${VAR:-…/Cosmos3-Nano}` bare-base to a non-`/models/base`
   target; the overlay file / `WITH_REASONING` / `up-fp8-reasoning` / BF16 env; a transitive overlay
   `include:`; reasoner-util 0.85→0.70) and each flipped the relevant `tests/deploy` assertion RED, then
   restored the tree byte-identical. The wiring guards have teeth.
5. **INV-7 (unverified mode default-on)** — disproved. `make up-fp8` enables exactly the FP8-gated modes
   (t2i / reasoning AM-S2 PASS / action AM-S3 PASS); NVFP4 is out of scope (renderable, not GPU-verified).
6. **INV-8 (schema drift)** — disproved (`openapi.json` unchanged at working-tree and index).
7. **Blast radius / forbidden files** — disproved (all changes in `allowed_files`; no README/webui/schema/
   archive edit).
8. **CPU suite** — green (exit 0).
9. **R-08 BF16 mislead** — the `~26 GiB BF16 reasoner` footprint is reconciled to FP8/KV-dominated.

## Findings (both fixed; neither breached the gate)

- **F1 — stale `CoResidencyContract.eviction="process_kill"`** (`api/engines/vllm/coresidency.py`): the
  prose was reconciled to "container STOP" but the structured Data field still said `process_kill` — a
  prose↔Data contradiction (the exact "mislead a future reader" hazard R-08 targets). **FIXED:** field →
  `container_stop` (+ a note that the dormant subprocess path is process-kill) + the pinning test updated.
- **F2 — P1 over-cited unwritten records**: `evidence/P1` said the ResidencyId-label finding was "recorded
  as an eval seed + R-08 note + handoff follow-up", but those close-out docs were not yet written at the
  time of the verifier's read. **FIXED:** the close-out docs (`evidence_map`/`risk_register`/
  `eval_seed_cases`/`handoff`) were written, making the citations true.

## Strongest counterexample
F2 — the evidence advertised a paper trail the diff had not yet written (close-out docs byte-frozen from
before the smoke). A documentation/citation gap, not a technical breach. Resolved by writing the docs.

## Outcome
Technical done condition **holds**; no falsification. Two honest documentation defects fixed. Combined
with the owner quality PASS (Feng, 2026-07-26) → **GATE-AM-S4-ORCHESTRATION PASSES**.
