# Session Handoff

## State Snapshot

- Session: MIG-S8, Release Gate, Evidence Review, and Handoff
- Branch: WebUI repo `session-8` (local commits only; **not pushed** — `origin/main` = seed `c3983f7`)
- Last commit at close: `docs(s8): adversarial verification (fresh context) = PASS` (`0529193`)
- S8 commits (6): `85e2b9a` refining pack · `063e4df` outputs (matrix/checks/evidence/gate) ·
  `a39a856` reconcile evidence/risk/eval/checklist · `1f43ecf` sharded review + in-radius fixes ·
  `348a177` amendments S8-A1/S8-A2 · `0529193` adversarial verification.
- Changed files (all within `allowed_files` + amendments S8-A1/S8-A2):
  - **Outputs:** `docs/session_8/outputs/{acceptance_matrix,deterministic_checks,evidence_review,gate_record}.md`.
  - **Refining pack + review:** `docs/session_8/{brainstorming,proposal,design,tasks,plan,execution_contract}.md`,
    `docs/session_8/specs/*.md` (6), `docs/session_8/{failure_arbiter,sharded_review,adversarial_verification}.md`.
  - **Reconciled:** `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
    `docs/release_checklist.md`, this handoff.
  - **Amendment S8-A1 (owner-approved):** scrubbed `/workspace/…` local paths from
    `docs/session_{2,3,4}/**` (9 files).
  - **Amendment S8-A2 (owner-approved):** `tests/test_private_ref_scan.py` (+`workspace_path`
    pattern +`.webm`, RED-before-GREEN tests); `docs/session_8_contract.yaml` (allowed_files amend).
  - **Eval seeds:** `docs/eval_corpus/mig_s8_{scanner_abspath_blindspot,broken_scan_silent_pass}.md`.
- Checks run (host: RTX 5090 present, **no GPU inference this session** by owner decision):
  - **CPU checks re-run green:** `ruff check api tests` = 0; `pytest -m "not gpu"` =
    **486 passed / 0 failed / 0 skipped** (JUnit; 485 at S7 + 1 test added by S8-A2); webui
    `build`/`lint`/`typecheck` + **vitest 209**; `docker compose config` fp8+nvfp4 = exit 0 / 0-byte
    stderr. Evidence: `docs/session_8/outputs/deterministic_checks.md`.
  - **Scans clean:** committed `tests/test_private_ref_scan.py` = 0 findings (now covers the
    `/workspace/` class after S8-A2); weight/media tracked+tree scans empty; S8 broad-scan human
    gate (lockfile-URL / abspath / private-host) clean.
  - **Sharded review** (5 axes, read-only subagents): correctness = no findings; 8 findings
    total, all **resolved** in-session (in-radius fixes + owner-approved S8-A1/S8-A2). No
    unresolved High/Critical. `docs/session_8/sharded_review.md`.
  - **Adversarial verifier** (fresh context): **PASS** — reproduced every number, whole-tree
    leak scan clean, blast radius clean, all adversarial cases pre-empted.
    `docs/session_8/adversarial_verification.md`.
- Checks NOT run (recorded with reason):
  - All GPU inference (`EV-MIG-GPU-*`) + the vLLM-Omni image build — deferred manual gate
    (owner decision; `INV-8`). GitHub-hosted CI run — at-publish (nothing pushed). Live
    `git ls-remote`/HF revision resolution — network (pins internally consistent).
- Current status: **`GATE-MIG-S8-BETA` is ready for owner ratification with a recommended GO
  (public beta / research preview).** Every PRD MUST is covered (14 PASS / 2 BETA-LIMITED /
  0 NO-GO), claims tie to public evidence, no unowned release-blocking risk, GPU surface
  honestly beta-limited.

## Recommended verdict (owner ratifies)

**GO for public beta / research preview** — advisory; the owner records the binding decision.
GO rule met on all 8 clauses (`gate_record.md`): scrub clean ∧ CPU checks green ∧ compose
renders ∧ license/hygiene present ∧ every runtime claim evidence-qualified ∧ no unowned
release-blocking risk ∧ GPU surface beta-limited ∧ every PRD MUST covered.

**GO is conditional on** (not blockers — standing / post-publish):
1. **Standing beta-limited GPU gate** — the full GPU surface is unverified; run the GPU session
   before implying verified support (below).
2. **At-publish items** (`release_checklist.md` §9) — enable GitHub Private vulnerability
   reporting; confirm CI badge + `security/policy`/`discussions` links resolve once public; set
   About/topics; tag + release notes.
3. **At-publish CI confirmation** (§5) — `ci.yml` green on the GitHub-hosted runner (locals green).

**The single lever that flips this to NO-GO:** if the owner requires passing GPU evidence
*before* any public exposure. No other release blocker is open.

## Evidence bundle (for ratification)

- Acceptance matrix: `docs/session_8/outputs/acceptance_matrix.md` (every PRD MUST).
- Deterministic checks: `docs/session_8/outputs/deterministic_checks.md`.
- Evidence review: `docs/session_8/outputs/evidence_review.md` (claim → public evidence).
- Gate record: `docs/session_8/outputs/gate_record.md` (`GATE-MIG-S1..S8` + recommended verdict).
- Sharded review + Failure Arbiter + Adversarial verification: `docs/session_8/*.md`.

## Final pins / revisions (any later GPU run MUST match these)

- vLLM-Omni fork commit: `697035018b70cef76b974a909d23371a9984c3f2`
- FP8 `wfen/Cosmos3-Nano-FP8-Blockwise` @ `4e181f996abf03f3425298ef692e6e5e56fd46a4` (license `openmdw-1.0`)
- NVFP4 `wfen/Cosmos3-Nano-NVFP4-Blockwise` @ `b5c9332efbaefa72c99890b1b1150da12ca9256c` (license `openmdw-1.0`)
- BF16 base `nvidia/Cosmos3-Nano` @ `fea6e03ac3d7884b4105ed8ee79fc480fca70965` (license `other`)

## Manual GPU result summary

**None run this session** (owner decision to defer). All `EV-MIG-GPU-*` cases are
**NOT-YET-RUN / beta-limited**; the README marks every generation/reasoning/action mode
GPU-unverified (`INV-8` satisfied). Required per-run evidence fields: hardware, driver/CUDA,
checkpoint repo+revision, vLLM-Omni commit, request shape, artifact metadata, pass/fail (`NFR-6`).

## Decision Log

| Decision | Chosen | Rejected | Reason | Ref |
|---|---|---|---|---|
| GPU gates | Review-only / defer (beta-limited) | Run GPU now / hybrid | Owner decision 1; `INV-8` permits manual gates for beta | brainstorming Q1 |
| GO/NO-GO authorship | Recommend, owner ratifies | Verdict blank / owner-states-now | Owner decision 2; `GATE-MIG-S8-BETA` is a human gate | brainstorming Q2 |
| Acceptance framing | Per-PRD-MUST matrix + gate view | Gate-keyed only | acceptance criterion "covers every PRD MUST" | design D-2 |
| Path leak `/workspace/…` (FA-2) | Scrub historical docs (amend S8-A1) | Accept non-blocking / defer | Owner chose scrub; clean public release | `failure_arbiter.md` FA-2 |
| Scanner gap (FA-3) | Patch scanner now (amend S8-A2) | Defer (eval seed only) | Owner chose patch; makes the gate durable | `failure_arbiter.md` FA-3 |
| Check #15 broken scan (FA-1) | Rewrite with exact cmd+exit codes | Leave prose "clean" | TEST_BUG: a scan that can't fail is not evidence | `failure_arbiter.md` FA-1 |

## Next Priority Queue

1. **GPU session (release-critical):** run the `EV-MIG-GPU-*` manual gates on the RTX 5090 at the
   pins above (record all `NFR-6` fields); build `deploy/vllm-omni.Dockerfile`
   (`docker compose -f deploy/docker-compose.fp8.yml build vllm-omni`) + confirm its serve
   entrypoint; resolve drift **D1** (does the default `vllm_omni` container load the public FP8
   **and** NVFP4 checkpoints). Re-affirm/adjust the README's per-mode beta-limited markings.
2. **At-publish tasks** (`docs/release_checklist.md` §9): Private vulnerability reporting; CI
   badge + self-referential links resolve; About/topics; tag + release notes; owner GO/NO-GO.
3. **Hardening (R-16):** evaluate `docker-socket-proxy`; decide the non-loopback exposure policy
   (`X-API-Key` enforceable end-to-end after S7's X-1 fix).
4. **Scanner + `deploy/` CI gate (T-1 + S8 verifier residual):** extend the committed scanner's
   **`SCAN_ROOTS`** to `deploy`, `tools`, and root files (it currently covers only
   `api/webui/tests/schemas/docs/.github`), and add a render-only + weight-copy + private-path CI
   job for `deploy/`. The S8 verifier independently confirmed those roots are clean **now**, but
   the committed gate does not guard them. (Product/CI change → contract amendment.)
5. **External HF cleanup (drift D3):** the public checkpoint repos ship dev-scratch (`_s2_*`) /
   provenance / loader-script files — an owner HF-side cleanup, external to this repo.

## Warnings And Gotchas

- **Amendments need owner sign-off:** S8-A1 (historical-doc scrub) + S8-A2 (scanner patch) were
  owner-approved this session and recorded in `docs/session_8_contract.yaml`.
- **A scan is only evidence if it records the exact command + exit code and is proven to fail on a
  counterexample.** S8 check #15's abspath sub-scan used an unsupported `rg` look-around under
  `2>/dev/null` and silently passed (TEST_BUG, FA-1). Never gate on `2>/dev/null` scans; prefer
  the committed exit-coded scanner. (`docs/eval_corpus/mig_s8_broken_scan_silent_pass.md`.)
- **Do not embed a real local path even as a negative example.** Writing `/data/home_<user>` /
  `/workspace/…` literals in a review/arbiter/eval doc trips the scanner — redact them.
- **The committed scanner's covered surface is itself reviewable:** its `PRIVATE_PATH_PATTERNS`
  missed `/workspace/` (fixed, S8-A2) and its `SCAN_ROOTS` still omit `deploy/tools/root-files`
  (queue #4). A release gate must run an independent, wider scan — do not trust "scan clean" from
  a fixed pattern+root list alone. (`docs/eval_corpus/mig_s8_scanner_abspath_blindspot.md`.)
- **Files future sessions must not casually edit:** `api/**` + `schemas/openapi.json` (`INV-9`
  public shape); `pyproject.toml`/`uv.lock`/`package.json` pins (`INV-10`). No private paths/hosts
  in scanned docs (`/path/to/…` is the only sanctioned absolute placeholder).
- **Deferred risks:** R-05 (GPU unproven) / R-08 (surface breadth) / R-13 (vLLM-Omni image) /
  R-16 (socket hardening) — all owner-dispositioned beta-limited, routed to the GPU/hardening
  sessions; drift D1 → GPU session; drift D3 → external.

## Eval Seeds

- New regression candidates (`docs/eval_corpus/`):
  - `mig_s8_scanner_abspath_blindspot.md` — a private-path scanner's covered pattern+root set is
    a blind spot; a release gate must run an independent wider scan (found 25 `/workspace/…` leaks).
  - `mig_s8_broken_scan_silent_pass.md` — a scan using unsupported regex under `2>/dev/null`
    reports "clean"; record command+exit code and prove-it-can-fail.
- Instruction-update candidates (REVIEW.md / project-contract template): (a) a release-gate scan
  is evidence only if it records the exact command **and** exit code and is proven to fail on a
  counterexample — never `2>/dev/null`; (b) a scrub scanner's pattern set **and** root set are
  reviewable artifacts — run an independent wider scan at the release gate; (c) redact real local
  paths even in review/eval docs (recurrence of the S3 docs-scrub lesson).
