# AM-S6 Tasks

Ordered by dependency. Each task is verifiable. Specs: `docs/session_6/specs/*`. Design: `design.md`.

## 1. Verification tooling (write the check first)
- [ ] 1.1 Add a relative-link + anchor resolver (`docs/session_6/check_links.py`) over `README.md`,
  `docs/walkthrough.md`, `docs/model_setup.md`: resolve relative file links + GitHub-slug `#anchors`;
  exit non-zero on any break. (spec: docs-links-and-license · "All internal links resolve")
- [ ] 1.2 Prove it fails on a deliberately broken link, then passes on the real docs (negative control).

## 2. License reconciliation (source of truth first)
- [ ] 2.1 `docs/model_setup.md` §1 table: base `nvidia/Cosmos3-Nano` license → **OpenMDW 1.1** + HF-tag
  note. (spec: docs-links-and-license · "Base license is OpenMDW 1.1 everywhere")
- [ ] 2.2 `docs/model_setup.md` §2 Licensing: code MIT / quantized OpenMDW 1.0 / base OpenMDW 1.1,
  stated once; keep INV-7 "weights are not MIT".

## 3. README honest status + "See it in action"
- [ ] 3.1 Update the Features table statuses (t2i/t2v/i2v/t2v_audio, Reasoning, Action → GPU-verified
  FP8+NVFP4) and the footnote. (spec: readme-see-it-in-action · "Verified set ⊆ owner-passed set")
- [ ] 3.2 Replace the Status & security verification bullets with the 2×3 per-mode × per-format matrix;
  remove the obsolete video-smoke caveat.
- [ ] 3.3 Fix the stale spots: top NOTE box, Quickstart "other modes not yet", the `<details>`
  `make up-fp8-reasoning`/"adds the BF16 base" line, and the checkpoint-table base row + "reasoning and
  action also use the BF16 base" prose. (spec: readme-see-it-in-action · "Stale pre-phase claims gone")
- [ ] 3.4 Add the `## See it in action` section after Features + the Jump-to nav anchor; no inlined
  screenshot. (spec: readme-see-it-in-action · "Section present / Jump-to / no screenshot")
- [ ] 3.5 Reconcile the README Licensing note to OpenMDW 1.1 (base) / 1.0 (quantized).

## 4. docs/walkthrough.md (UI-first, ADHD)
- [ ] 4.1 Setup-once preamble (`make up-fp8`/`up-nvfp4`, `make health`, open `:3000`); TL;DR + anchors.
  (spec: walkthrough-per-mode · "Setup preamble" / "ADHD structure present")
- [ ] 4.2 Studio section: t2i fully worked + compact video block (drafted prompts, attested output) +
  placeholders `studio-{t2i,t2v,i2v,t2v_audio}.png` + `<details>` API pointer.
- [ ] 4.3 Reasoning section: recorded prompt → recorded answer + `reasoning-chat.png` + API pointer.
- [ ] 4.4 Action section: forward_dynamics worked (Embodiment/Mode/Run demo → rollout + 3D view) +
  one-liners for policy & inverse_dynamics + placeholders `action-{forward_dynamics,policy,inverse_dynamics}.png`
  + `<details>` pointer to `docs/session_3/action_demo_runbook.md`.
  (spec: walkthrough-per-mode · "Every verified mode present with input + expected output")

## 5. Evidence / risk / eval / handoff
- [ ] 5.1 `docs/evidence_map.md`: add the AM-S6 audit row + the dated owner **video amendment** (t2v/i2v/
  t2v_audio × FP8+NVFP4, Feng 2026-07-26); resolve E-14 (OpenMDW 1.1) as fact.
- [ ] 5.2 `docs/risk_register.md`: close R-06 / R-09 / R-13 for AM-S6.
- [ ] 5.3 `docs/eval_seed_cases.md`: mark EV-AM-README-VERIFIED-SUBSET / EV-AM-WALKTHROUGH-STRUCTURE /
  EV-AM-DOCS-LINKS-RESOLVE exercised; add any AM-S6 harvest.
- [ ] 5.4 `docs/handoff.md`: rewrite for AM-S6 (state, matrix incl. video, placeholder list, residual risks).

## 6. Checks + review
- [ ] 6.1 Run the 4 deterministic checks + the link resolver; all green.
- [ ] 6.2 Sharded review (correctness/readability/security/tests/architecture/performance, read-only).
- [ ] 6.3 Adversarial honesty pass (fresh context): falsify the done condition / find surviving
  over-claim or lost caveat.
- [ ] 6.4 Fix High/Critical findings only; re-run checks.
- [ ] 6.5 Verify `GATE-AM-S6-DOCS`; finalize handoff + eval seeds.
