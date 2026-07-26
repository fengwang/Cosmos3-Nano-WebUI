# AM-S6 Plan (executable)

TDD for docs: write the deterministic check, watch it fail, edit docs, watch it pass. Specs:
`docs/session_6/specs/*`. Commit points are checkpoints only (owner reviews/commits, per prior sessions).

## Step 0 — baseline (RED)
```bash
rg -n "GPU-verified" README.md                       # currently: only t2i verified
rg -n "up-fp8-reasoning|adds the BF16 base|reasoning and action also use the BF16 base" README.md  # stale refs present
test ! -e docs/walkthrough.md && echo "walkthrough absent (expected)"
```

## Step 1 — link resolver (Task 1) — write the failing check first
Create `docs/session_6/check_links.py` (stdlib only; GitHub slug rules: lowercase, strip punctuation
except `-`/space, spaces→`-`). It scans README.md, docs/walkthrough.md, docs/model_setup.md for
`](target)`; for `#frag` it checks the slug set of the *target* doc (same file if bare `#`); for relative
paths it checks existence (repo-root relative, ignoring `http(s)`/`mailto`). Exit non-zero on any break.
```bash
uv run python docs/session_6/check_links.py            # RED now (walkthrough.md missing → and after edits: GREEN)
# negative control:
uv run python docs/session_6/check_links.py --selftest  # injects a broken anchor → expect non-zero
```
Commit point: `docs(am-s6): link+anchor resolver (neg-control proven)`.

## Step 2 — license reconciliation (Task 2)
Edit `docs/model_setup.md`:
- §1 table row `nvidia/Cosmos3-Nano`: `other` → `OpenMDW 1.1` and add a footnote: *HF `license:` tag is
  `other` (OpenMDW is not in HF's SPDX list); `license_name: openmdw1.1-license`, https://openmdw.ai/license/1-1/*.
- §2: "openmdw-1.0 for FP8/NVFP4; **OpenMDW 1.1** for the `nvidia/Cosmos3-Nano` base"; keep "weights are
  not MIT" (INV-7).
```bash
rg -n "OpenMDW|openmdw|\bother\b" docs/model_setup.md   # base=1.1, quantized=1.0, no bare-other base
```

## Step 3 — README status + See-it-in-action (Task 3)
Edit `README.md`:
- Features table rows → `GPU-verified` (FP8+NVFP4) for t2i/t2v/i2v/t2v_audio, Reasoning, Action; rewrite
  footnote ¹ (drop "only text→image"; cite AM-S2..S5 + owner PASS + the 2026-07-26 video attestation).
- Status & security: replace the two verification bullets with the 2×3 matrix; delete the "720p smoke
  does not promote video" caveat.
- NOTE box (top): "all three modes GPU-verified on FP8 + NVFP4; trusted-LAN, no-auth" (keep the security
  caveat, drop "only text→image").
- Quickstart: drop "the other modes are not yet"; `<details>` → "all modes on `make up-fp8`/`up-nvfp4`
  (zero-BF16)"; remove `make up-fp8-reasoning`.
- Checkpoint table: drop the BF16-base row (keep FP8/NVFP4 rows); prose "reasoning and action also use
  the BF16 base" → "reasoning and action are served off the same quantized checkpoint (no BF16 base)".
- Licensing note: quantized OpenMDW 1.0; legacy base OpenMDW 1.1; code MIT.
- Add `## See it in action` after `## Features` (prose, per-mode, links `docs/walkthrough.md`,
  no `![...]`); add `[See it in action](#see-it-in-action)` to the Jump-to nav.
```bash
rg -n "GPU-verified" README.md                          # all six modes; subset of owner-passed
rg -n "up-fp8-reasoning|adds the BF16 base|reasoning and action also use the BF16 base|only \*\*text" README.md  # → no matches
rg -n "^## See it in action" README.md                  # exactly 1
```
Commit point: `docs(am-s6): README honest all-modes status + See it in action + license`.

## Step 4 — docs/walkthrough.md (Task 4)
Create `docs/walkthrough.md`: TL;DR; "Jump to" anchors; **Setup once**; per-mode sections per
`design.md` §D; 8 `![...](docs/images/<mode>-<example>.png)` placeholders; each mode a `<details>` API
pointer (blank line after `</summary>`). Expected-output prose copied from:
- t2i → `docs/session_2/evidence/P3` + model_setup §6 (`480x480`, studio photo).
- reasoning → `docs/session_2/evidence/P2` (`Red, Blue, Yellow`) / `docs/session_4/P1` (gripper-friction).
- action FD/policy/ID → `docs/session_3/action_demo_runbook.md` + `evidence/P1,P2`.
- video → owner attestation level only ("~1280×720, ~49 frames; t2v_audio adds audio").
```bash
rg -n "docs/images/" docs/walkthrough.md                # ≥1 per mode, all under docs/images/, <mode>-<example>.png
git status --porcelain docs/images                      # empty (no binary)
uv run python docs/session_6/check_links.py             # GREEN
```
Commit point: `docs(am-s6): docs/walkthrough.md — per-mode example→expected + placeholders`.

## Step 5 — evidence/risk/eval/handoff (Task 5)
- `docs/evidence_map.md`: AM-S6 audit row; **E-14 resolved → OpenMDW 1.1** (cite the 3 HF fetches);
  dated **video amendment** row (t2v/i2v/t2v_audio × FP8+NVFP4, owner PASS Feng 2026-07-26).
- `docs/risk_register.md`: R-06 / R-09 / R-13 → Closed (AM-S6), with the closing evidence.
- `docs/eval_seed_cases.md`: EV-AM-README-VERIFIED-SUBSET / -WALKTHROUGH-STRUCTURE / -DOCS-LINKS-RESOLVE
  → exercised (result), + AM-S6 harvest (video-amendment honesty seed).
- `docs/handoff.md`: rewrite for AM-S6 (matrix incl. video, placeholder list in walkthrough order,
  residual risks + archive note).

## Step 6 — full checks + review + adversarial (Task 6)
```bash
rg -n "GPU-verified" README.md; rg -n "docs/images/" docs/walkthrough.md
git status --porcelain docs/images; uv run python docs/session_6/check_links.py
```
Then sharded review → `docs/session_6/sharded_review.md`; adversarial honesty pass (fresh context) →
`docs/session_6/adversarial_verification.md`; fix High/Critical; re-run; verify `GATE-AM-S6-DOCS`.
Final commit point: `docs(am-s6): close session — review/adversarial PASS, evidence/risk/eval/handoff`.
