# Session 4 Sharded Review

Date: 2026-07-06
Session: MIG-S4
Risk: high → 5-axis sharded review over the diff `4b868d1..HEAD` per
`docs/agent_workflow/prompts/sharded_review.md`. Each reviewer was read-only.

## Outcome

**No Critical or High findings on any axis.** Security/safety = clean (R-01 did not
recur). Correctness, tests, architecture, and performance each returned Medium/Low/Nit
accuracy or traceability findings. Because the docs *are* the deliverable on this HIGH-risk
gate, all substantive Medium/Low findings were fixed (not just High/Critical); nits were
fixed where near-zero-cost. Deduplicated findings and dispositions below.

## Findings (deduplicated)

| # | Axis | Sev | Finding | Disposition |
|---|---|---|---|---|
| R1 | Correctness | Medium | `hf_verification.md`/`evidence_map.md` cited "7 BF16 shards" for the base repo, but the probe recorded only `has_transformer: true` — the count was not in the cited artifact. | **Fixed:** probe now records `transformer_files` for reachable base repos (`evidence.json` shows 7 `diffusion_pytorch_model-*-of-00007.safetensors` shards); the claim is now evidence-backed. |
| R2 | Correctness | Low | `hf_verification.md` NVFP4 `verify_precision` cell asserted a `ValueError` for a path never reached (discovery raises `FileNotFoundError` first in `build_oracle`). | **Fixed:** cell now reads "n/a — never reached (discovery raises first)"; added a note that `build_oracle` calls discovery before verify. |
| R3 | Tests | Low/Med | Probe `--check` did not pin the exact-`"fp8"` recipe semantic that D1/FA-2 rests on (a `startswith` regression still passed). | **Fixed:** added `assert precision_from_quant_config({"recipe":"fp8_blockwise_mixed"})[0] is Precision.UNKNOWN`. |
| R4 | Tests | Low | Probe `--check` did not isolate `oracle_loadable`'s discovery guard (the negative case varied all three inputs at once). | **Fixed:** added `assert oracle_loadable(MISSING, True, FP8) is False`. |
| R5 | Architecture | Low | `design.md` still asserted the FA-1-refuted "non-public base → beta-limited" premise, unannotated; ACD blueprint named symbols the built probe does not use. | **Fixed:** added a "Post-verification note" to `design.md` (FA-1/FA-2 supersession + as-built deltas); added a frozen-snapshot pointer to `brainstorming.md`. |
| R6 | Correctness/Arch | Nit | `discover_transformer_dir` cited as `loader.py:43-49`; the function spans `33-50`. | **Fixed:** corrected to `loader.py:33-50` in `hf_verification.md`, `drift_report.md`, `failure_arbiter.md`, and the eval seed. |
| R7 | Correctness/Tests | Nit | Probe docstring + layout spec said header precision "mirrors `observe_precision` (absent ⇒ FP8)", but the probe returns UNKNOWN on a raw header with no `weight_quantizer` key. | **Fixed:** reworded the probe docstring and the spec scenario to describe the deliberate UNKNOWN behavior. |
| R8 | Performance | Low/doc | The `local == public` SHA gate's cost (~34 GB / ~80s with a local mount, 0 without) was not quantified. | **Fixed:** added the cost note to the `--no-hash` help string and the probe docstring. |
| R9 | Security | — | Full scan clean: no dev-variant/host-path/secret leak; `producer_provenance.json` recorded by filename only; probe `subprocess` safe (list args, no shell); blast radius respected. | No action (clean). |

## Notes

- The private-value regression flagged three pre-existing `git@github.com:fengwang/…`
  references in `docs/evidence_map.md` (public GitHub org for the target repo + vLLM-Omni
  fork). These are legitimate public remotes cited throughout the blueprint, not private
  leaks, and are **not** part of the Session 4 diff. The canonical detector set (no
  over-broad bare `feng`) is clean over all Session 4 content.
- After fixes: `verify_hf_checkpoints.py --check` passes; the full probe re-runs to exit 0;
  the deterministic checks and the canonical private-value regression are clean.

## Re-check after fixes

- `python3 docs/session_4/probes/verify_hf_checkpoints.py --check` → OK (now 16 pure-core assertions).
- Full probe → exit 0; `evidence.json` regenerated (base `transformer_files` present).
- Canonical private-value regression over `docs/session_4/**` + `docs/model_setup.md` + edited shared docs → clean.
