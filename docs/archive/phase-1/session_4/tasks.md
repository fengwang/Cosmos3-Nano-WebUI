# Session 4 Tasks - Hugging Face Checkpoint Verification and Model Setup Docs

Session: MIG-S4
Derived from: `specs/*.md` (what) + `design.md` (how)

## 1. Verification probe (evidence source)

- [ ] 1.1 Write the pure-core calculations in `docs/session_4/probes/verify_hf_checkpoints.py`
      (parse via reused `parse_header`, `precision_from_quant_config`,
      `precision_from_header_keys`, `crosscheck`, `evaluate_layout`, `derive_drift`,
      `scrub`, `build_bundle`, `render_summary`) with an in-file `--check` mode that
      runs the spec-derived assertions and exits non-zero on failure.
- [ ] 1.2 Write the thin action shell (revision resolve, `HfApi` metadata,
      `list_repo_files` + `get_paths_info`, partial local header reads, JSON/summary write).
- [ ] 1.3 Run the probe against the two public repos + base-repo reachability; emit
      `docs/session_4/probes/evidence.json` and `summary.md`; confirm `--check` passes.

## 2. Verification note

- [ ] 2.1 Write `docs/session_4/hf_verification.md` from the evidence bundle
      (revisions, license, card state, full layout, self-containment, header/quant
      results, `local==public` cross-check, citations).

## 3. Model setup contract

- [ ] 3.1 Write `docs/model_setup.md` (repo IDs + revisions, `COSMOS3_*` env table,
      mount layout, self-containment, license separation, per-mode compatibility
      matrix, drift caveats, minimal operator notes; defer prose to S7, Docker to S6).

## 4. Drift report

- [ ] 4.1 Write `docs/session_4/drift_report.md` (D1 NVFP4↔FP8 asymmetry, D2 non-public
      base, D3 external-repo hygiene, D4 empty NVFP4 card) each with severity,
      disposition, and routed risk row.

## 5. Evidence / risk / eval updates

- [ ] 5.1 Add rows to `docs/evidence_map.md` (FP8/NVFP4 revisions, license, layout,
      drift, verification date).
- [ ] 5.2 Update `docs/risk_register.md` R-03 and R-04; add rows for D1/D3 if warranted.
- [ ] 5.3 Add EV-MIG-HF-FP8-METADATA and EV-MIG-HF-NVFP4-METADATA to
      `docs/eval_seed_cases.md` and `docs/eval_corpus/`; add any caught/missed seed.

## 6. Verification and review

- [ ] 6.1 Run full deterministic checks (ls-remote x2, `hf_hub` version, `rg` repo IDs
      in docs) + probe `--check` + private-value regression over `docs/session_4/**`;
      classify any failure via the Failure Arbiter.
- [ ] 6.2 Sharded review (correctness / security / tests / architecture / performance);
      save `sharded_review.md`; fix only High/Critical; re-check.
- [ ] 6.3 Adversarial verification (fresh context, contract+diff+evidence only);
      save `adversarial_verification.md`.

## 7. Close

- [ ] 7.1 Verify the done condition (`GATE-MIG-S4-HF`); write/update `docs/handoff.md`;
      add eval seeds; state remaining risks and next-session warnings.

## Ordering / dependencies

1.1 → 1.2 → 1.3 gate everything (evidence first). 2/3/4 consume the bundle and can be
authored together. 5 follows 2–4. 6 after 5. 7 last. Commit at clean checkpoints
after 1.x, after 2–4, after 5, and after 6–7.
