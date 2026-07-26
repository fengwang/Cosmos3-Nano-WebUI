# AM-S6 Sharded Review — README "See it in action" + docs/walkthrough.md (docs-only)

Reviewer: read-only sharded code reviewer (no implementation-conversation context).
Scope: working-tree diff vs `docs/session_6_contract.yaml` / `docs/session_6.md`, the project
contract (INV-1..INV-9), PRD (FR-7/FR-9, Decision 6/8), and the recorded AM-S2..S5 evidence.
Date: 2026-07-26.

## Verdict

**No Critical or High findings.** The session meets `GATE-AM-S6-DOCS`: README has a lean
"See it in action" section linking `docs/walkthrough.md`; the walkthrough is per-mode
example-input→expected-output with 9 `docs/images/…` placeholders and no committed binary; the
BF16-base license is reconciled to **OpenMDW 1.1** consistently; every internal link/anchor
resolves; and the required caveats are preserved. Findings below are all Low/Nit.

The one load-bearing item — the video sub-modes (t2v/i2v/t2v_audio) promoted to "GPU-verified on
both FP8 and NVFP4" — is an **owner-authorized, dated amendment** (Feng, 2026-07-26), recorded in
`docs/evidence_map.md` AM-S6 audit and scoped to exactly the 3 video modes × 2 formats the owner
named. Per the session mandate this amendment is authorized, so it is **not** an over-claim
(INV-6/INV-7 satisfied by the owner-authority route, PRD Decision 6). See F-2 for the residual
honesty nuance (informational).

## Verification performed (deterministic evidence)

- **Blast radius (PASS).** `git status --short`: only `README.md`, `docs/model_setup.md`,
  `docs/evidence_map.md` modified; `docs/walkthrough.md` + `docs/session_6/` new. All inside
  `blast_radius.allowed_files`. No `api/**`, `webui/**`, `deploy/**`, `Makefile`, `.env.example`,
  `schemas/openapi.json`, or `docs/archive/**` touched.
- **INV-1 / NFR-1 no image binary (PASS).** `git status --porcelain docs/images` → empty; no
  `docs/images/` directory exists. All 9 walkthrough image links are `docs/images/<mode>-<ex>.png`
  placeholders (`rg docs/images/ docs/walkthrough.md`).
- **Link resolver (PASS + negative control).** `uv run python docs/session_6/check_links.py` →
  exit 0 ("all relative links and anchors resolve in README.md, docs/walkthrough.md,
  docs/model_setup.md"). `--selftest` → exit 0 and correctly reports the deliberately broken anchor
  `#does-not-exist` (the check is not a no-op). Cross-file anchors verified (e.g.
  `README.md#status--security` → README `## Status & security`). All README relative targets exist
  (`LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `misc/logo.png`, the docs).
- **R-09 license single/consistent (PASS).** BF16 base `nvidia/Cosmos3-Nano` = **OpenMDW 1.1** in
  both `README.md:175` and `docs/model_setup.md:15,17-22,36-37`; quantized `wfen/*` = **OpenMDW 1.0**
  everywhere. The bare HF `other` tag is explained (not in HF's SPDX picklist) with
  `license_name: openmdw1.1-license` + link. No lingering unexplained bare `other`. Reconciled
  against the HF model card (the blueprint's designated tie-breaker), superseding both the prior
  bare-`other` doc claim and the owner's earlier `openmdw-1.0` recollection (E-14 closed).
- **R-13 claim↔evidence fidelity (PASS).** Every walkthrough "expected output" traces to a recorded
  run:
  - t2i "one 480×480 PNG … GPU-verified under `GPU-S3`" — matches E-11 / model_setup §6 t2i row and
    the AM-S2/S4 480×480 PNG runs.
  - Reasoning quote *"…the lack of friction between the gripper and the cup's surface…"* — verbatim
    from `docs/session_4/evidence/P1-allmodes-smoke-gpu.md:29`.
  - Reasoning `Red, Blue, Yellow` — from AM-S2 P2 and AM-S5 P2 coherence probes.
  - Action FD "~0.6 MB, 17 frames at 10 fps" — matches AM-S3 P1 ("valid 621 KB MP4 rollout") +
    runbook `num_frames=17, fps=10`; policy `[16,29]` and ID `[60,9]` match AM-S3 P1 / AM-S5 P1.
  - Video expected-output is kept at the **generic/default-derived** level (~1280×720, ~49 frames,
    "follows the prompt", "adds a matching soundtrack") — no fabricated artifact bytes; consistent
    with the amendment's stated "video expected-output stays at the owner-attested level (R-13)."
- **INV-6 subset (PASS, given the amendment).** Every README "GPU-verified" claim (`rg GPU-verified
  README.md` — top NOTE, Features table 4 rows + footnote, Status 2×3 matrix) is within the
  owner-passed set once the AM-S6 video amendment is admitted. The footnote (README:123-126)
  attributes each mode honestly: t2i→`GPU-S3`, video→owner PASS 2026-07-26, reasoning→AM-S2/S5,
  action→AM-S3/S5.
- **Caveats preserved (PASS — no honesty regression).** Guardrails-off (README:225-227,
  walkthrough:13-15), no-auth (README:218-219), loopback-by-default (README:220-221),
  one-stack-at-a-time (README:189,212; walkthrough:19). The obsolete "720p smoke does not promote
  video to verified" caveat was removed — this is the intended, amendment-authorized change, not a
  dropped safety caveat.
- **FR-9 / ADHD posture (PASS).** README stays a single lean file, no inlined screenshots (only the
  logo). Walkthrough has a **TL;DR**, a **Jump to** anchor row, fenced code blocks with `bash`
  language ids, and 3 `<details>`/`<summary>` blocks each with a blank line after `</summary>`
  (verified). Scannable per-mode structure.
- **Security / NFR-1 (PASS).** No secret/token/credential introduced. No *new* private absolute
  path: the only `/data/models/…` occurrences are (a) pre-existing documented mount-convention text
  in `model_setup.md:50,71` ("convention; any path via env") and (b) the pre-existing AM-S5 audit
  hardware line at `evidence_map.md:223` — neither added by AM-S6, and both are the public
  `/data/models/<Repo>` convention, not a private host path.
- **API route sanity (PASS).** App-layer routes cited in the walkthrough `<details>` blocks resolve
  in `schemas/openapi.json` (`/v1/generation/t2i`, `/v1/reason`, `/v1/action/forward_dynamics`).
  `/v1/videos/sync` + `/v1/videos` are correctly described as the *underlying omni-container*
  endpoints (not the public REST surface), so their absence from `openapi.json` is expected, not a
  defect.
- **Handoff artifacts (PASS).** `docs/eval_seed_cases.md` carries the three AM-S6 seeds
  (EV-AM-README-VERIFIED-SUBSET, EV-AM-WALKTHROUGH-STRUCTURE, EV-AM-DOCS-LINKS-RESOLVE). The
  evidence_map AM-S6 audit records the placeholder set implicitly via the walkthrough and the gate
  result.

## Findings

### F-1 (Nit — tests/hygiene) — compiled-bytecode artifact inside the untracked blast-radius dir
- **Where:** `docs/session_6/__pycache__/check_links.cpython-312.pyc` (untracked; the parent
  `docs/session_6/` is entirely untracked `??`).
- **Contract:** INV-1 / NFR-1 posture ("only intended docs committed"); repo hygiene.
- **Impact:** Low. When the owner stages the new session pack (a natural `git add docs/session_6/`),
  the `.pyc` gets committed alongside the docs — a build artifact that does not belong in version
  control. Not a secret and not a functional problem.
- **Smallest safe fix:** `rm -rf docs/session_6/__pycache__` before staging, and/or add
  `__pycache__/` to `.gitignore` (or stage files explicitly, excluding `__pycache__`). The
  `check_links.py` source itself is fine to commit.
- **Confidence:** High (file present on disk; dir untracked).

### F-2 (Low — informational; owner-authorized, no change required) — video "GPU-verified" rests on an attestation that folds INV-6(i) and (ii) into one statement
- **Where:** `README.md:116,124-125,208`; `docs/walkthrough.md:57-59`; `docs/model_setup.md:95`;
  `docs/evidence_map.md:330-338`.
- **Contract:** INV-6 defines "GPU-verified" as *(i) a recorded end-to-end run on the RTX 5090*
  **and** *(ii) the owner's recorded manual quality PASS* — two distinct things.
- **Observation:** For t2i/reasoning/action every "verified" cell cites a **recorded run with
  artifact metadata** (PNG byte size, MP4 bytes, trajectory shape, peak VRAM) *plus* an owner PASS.
  For the video sub-modes the amendment records only the owner's attestation that they "were run …
  and judged high quality (2026-07-26)"; i2v and t2v_audio have **no independent recorded-run row**
  with artifact metadata anywhere in the evidence tree (the only archived video artifact is the
  phase-3 UX-S2 720p **t2v** smoke, `EV-UX-GPU-720-NVFP4-T2V`, 18,517 MiB — text→video only). So the
  video row's honest INV-6 shape is weaker than the other rows: (i) and (ii) are bundled into the
  owner's single sentence rather than separately recorded.
- **Why not a finding to fix:** This session's mandate explicitly authorizes the owner amendment
  (owner is the quality-gate authority, PRD Decision 6), the amendment is dated and scoped exactly
  to t2v/i2v/t2v_audio × FP8+NVFP4, and the walkthrough deliberately keeps video expected-output at
  the attested (generic) level rather than inventing artifacts. It is therefore recorded as an
  honest, owner-decided promotion — **not** an over-claim.
- **Suggested (optional) hardening:** when the owner fills the `docs/images/studio-{i2v,t2v_audio}.png`
  screenshots, capture the artifact metadata (resolution / frame count / byte size / peak VRAM) for
  i2v and t2v_audio into the evidence_map so the video row cites a recorded run like the others,
  fully closing INV-6(i) for those two sub-modes. No blocking action this session.
- **Confidence:** High (evidence tree searched; no i2v/t2v_audio recorded-run row exists).

## Adversarial honesty pass (per routing §5 / R-06) — result: PASS

Each pre-registered adversarial case checked and cleared:

- *A mode called "GPU-verified" though its owner gate was FAIL/unrecorded (INV-6):* No. Every claim
  maps to a recorded owner PASS (t2i via the Studio owner confirmations AM-S4/S5; reasoning AM-S2/S5;
  action AM-S3/S5; video via the dated AM-S6 amendment). See F-2 for the video nuance (authorized).
- *An NVFP4-format limitation omitted, implying NVFP4 all-modes (INV-7):* No omission — AM-S5 proved
  all three modes on NVFP4 with owner PASS; there is genuinely no residual NVFP4 limitation to hide.
  The matrix honestly shows NVFP4 = owner PASS across the board.
- *Walkthrough "expected output" for a mode/format that never ran (R-13):* No invented output; video
  prose stays at the attested/default level (see Verification, R-13).
- *Screenshot binary committed instead of a placeholder (INV-1):* No — `git status docs/images` empty.
- *BF16-license stated two ways across README ↔ model_setup (R-09):* No — OpenMDW 1.1 (base) /
  OpenMDW 1.0 (quantized) consistent everywhere.
- *A caveat (guardrails-off / no-auth / one-stack) dropped or softened while adding upbeat examples:*
  No — all preserved in both README and walkthrough.

## Checks run / not run

- **Run:** `git status --short`; full diff of the three tracked docs; read of all new files;
  `check_links.py` + `--selftest`; `rg GPU-verified README.md`; `rg docs/images/ docs/walkthrough.md`;
  `git status --porcelain docs/images`; provenance greps for every walkthrough expected-output;
  license-consistency grep; secret/private-path grep; API-route vs openapi cross-check;
  `</summary>` blank-line posture; eval-seed presence.
- **Not run:** rendered-Markdown visual QA in a browser (GitHub slug algorithm approximated by the
  resolver, which the contract accepts); no GPU runs (docs-only session, out of scope); did not
  re-verify the archived phase-3 720p smoke bytes beyond confirming the row exists.
