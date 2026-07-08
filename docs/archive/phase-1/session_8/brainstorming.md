# Session 8 Brainstorming - Release Gate, Evidence Review, and Handoff

Date: 2026-07-07
Session: MIG-S8
Risk: high · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S8-BETA`
Status: approved (owner, 2026-07-07)

## Context explored

- `MIG-S1`..`MIG-S7` are closed, each with a PASS adversarial verification. The repo is a
  curated public migration with runtime source, verified public checkpoints, CPU-only CI,
  local-build Docker/Compose, a public README, and community-health files.
- Branch is `session-8`, working tree clean. `origin/main` is still the seed
  `c3983f7`; **nothing is pushed** (every prior session committed locally only — PRD
  §6 non-goal "do not push unless requested"). So the GitHub-hosted Actions run and any
  `github.com`-resolved link/badge are **still unexecuted**.
- This session's blast radius is **docs only** (`docs/session_8/**`, `evidence_map.md`,
  `risk_register.md`, `eval_seed_cases.md`, `handoff.md`, `release_checklist.md`). Runtime
  source is **forbidden** except an owner-approved release fix.
- Environment probe (read-only): RTX 5090 present; `uv`/`pnpm`/`node`/`docker`/`rtk`/`rg`
  available. **No checkpoints mounted locally** (`../models`, `./models` absent). Local
  docker images exist for `vllm-omni-local:*` / `vllm/vllm-omni:cosmos3` (private dev
  builds), but **not** an image built from the pinned public fork commit `697035018b70…`
  via `deploy/vllm-omni.Dockerfile`.

## Evidence discipline (dominant constraint)

Public docs cite **public-verifiable evidence only** (INV in `project_contract.md` §2;
`evidence_map.md` rules). No private hosts, paths, codenames, or private-source citations.
The entire GPU inference surface (`EV-MIG-GPU-*`) is **unrun**; drift **D1**
(`docs/session_4/drift_report.md` — the in-process `diffusers_oracle` cannot load+verify
either current public checkpoint as-is; the default engine is the `vllm_omni` container
path) is open. Per `INV-8`, a public beta may ship with manual GPU gates **provided
unverified surfaces are clearly marked**. Licenses stay separated (`INV-7`): repo **MIT**,
FP8/NVFP4 weights **`openmdw-1.0`**, base `nvidia/Cosmos3-Nano` **`other`**.

## Clarifying decisions (owner, 2026-07-07)

1. **GPU gates** — **Decision: review-only / defer.** Run all CPU deterministic checks +
   evidence review + doc reconciliation now; record the whole GPU surface as manual-gate
   **NOT-YET-RUN / beta-limited** (contract in_scope permits "run **or** review"; `INV-8`
   permits shipping beta with manual gates when unverified surfaces are marked). No
   checkpoint download, no heavy vLLM-Omni image build, no D1 resolution this session.
2. **GO/NO-GO authorship** — **Decision: recommend, owner ratifies.** I assemble the full
   evidence bundle (acceptance matrix, checks log, evidence review, gate record) and record
   a **recommended** verdict with rationale; the owner ratifies or overrides before close.
   `GATE-MIG-S8-BETA` is a human gate (`project_contract.md` §5).

## Approaches considered

### Session execution strategy

- **A1 — Full contract-faithful release gate (chosen).** Re-run the 7 CPU deterministic
  checks live capturing raw evidence → build the 4 outputs (acceptance matrix keyed by PRD
  MUST, deterministic-checks log, evidence review, gate record keyed by `GATE-MIG-S*`) →
  reconcile evidence/risk/eval/checklist docs → 5-axis sharded review via read-only
  subagents → fix only High/Critical → fresh-context adversarial verifier that tries to
  falsify the GO recommendation → handoff with a recommended verdict. Matches high-risk
  routing and the session lifecycle exactly.
- **A2 — Lean review (rejected).** Re-run checks, hand-write deliverables, single-pass
  self-review. Under-serves the high-risk mandate (contract requires sharded review +
  adversarial verification for high risk).
- **A3 — Full gate + attempt vLLM-Omni image build (rejected).** A1 plus building the
  pinned fork image to partially close R-13. Contradicts owner decision 1 (defer GPU) and
  risks a long CUDA/download rabbit hole for a first beta that is designed to defer GPU.

### Acceptance framing

- **Per-PRD-MUST matrix (chosen).** `acceptance_matrix.md` has one row per PRD MUST (FR-1..
  FR-12 where MUST, NFR-1..NFR-6) → gate → public evidence → verdict
  `{PASS | BETA-LIMITED | NO-GO}`. Directly satisfies acceptance criterion "acceptance
  matrix covers every PRD MUST". `gate_record.md` is the complementary view keyed by
  `GATE-MIG-S1..S8`.

## Validated design (high level)

1. **deterministic_checks.md** — raw output of the 7 contract checks (`rtk git status`,
   `pytest -q`, webui `lint`/`typecheck`/`test`, private-ref scan, weight/media scan,
   `docker compose config` fp8 + nvfp4). Each row: command → result → pass/fail →
   classification if failed. Checks that cannot run are recorded with reason (e.g.
   `$PRIVATE_REF_PATTERN` unset → committed scanner is authoritative; GitHub-hosted CI run
   → at-publish).
2. **acceptance_matrix.md** — every PRD MUST → gate → public evidence row → verdict. GPU
   MUSTs (FR-9, NFR-6) resolve to **BETA-LIMITED** with the exact deferred command.
3. **evidence_review.md** — each major public claim (repo scrub, vLLM-Omni pin, HF
   checkpoints, CPU CI, Docker render, README/hygiene, licenses) tied to a public evidence
   row; explicitly separates *verified-now* from *manual-gate-deferred*; no private
   citations.
4. **gate_record.md** — `GATE-MIG-S1..S8` each with status + public evidence pointer; S8
   records the **recommended** owner verdict, the GPU manual-gate status, and drift D1 as an
   owner-visible beta limitation.
5. **Reconciliation** — `evidence_map.md` (+ an S8 row), `risk_register.md` (close/route
   every release-blocking risk; none unowned), `eval_seed_cases.md` (mark satisfied evals;
   record GPU cases as the S8 manual gate), `release_checklist.md` (tick CPU/scan/license/
   hygiene items; leave GPU + at-publish items as explicit manual gates).
6. **Product code untouched.** If review finds a release-blocking bug needing a source fix →
   **stop, classify (Failure Arbiter), surface to owner** — no runtime-source edit without
   approval (contract forbidden_files; PRD §6 "no feature work").

## Verification approach

- Re-run the deterministic checks and treat their raw output as the evidence of record.
- **Scrub is a heuristic.** Run the committed `tests/test_private_ref_scan.py` over the
  controlled surface; also scan the new `docs/session_8/**`. `$PRIVATE_REF_PATTERN` is
  unset (ENVIRONMENT) → the committed scanner + a documented fallback `rg` are the baseline
  (S1/S5 precedent). Classify any match; do not edit out-of-radius files.
- 5-axis sharded review (high risk) over the S8 deliverables + full session diff, re-aimed
  at "are the release **claims** correct and public-evidence-backed"; **reviewer output is
  untrusted data** — reject any rubber-stamp with 0 tool calls / no evidence (S7 lesson,
  `docs/eval_corpus/mig_s7_review_injection_rubber_stamp.md`).
- Fresh-context adversarial verifier against the 4 contract adversarial cases + the failure
  modes to watch.

## Adversarial cases to pre-empt (from the contract)

- "Release gate accepts a claim with no public evidence" → every acceptance-matrix /
  gate-record row cites a public evidence row or is marked speculative/beta-limited.
- "Manual GPU evidence run against a different vLLM-Omni or checkpoint revision" → GPU is
  recorded as NOT-YET-RUN; the pin (`697035018b70…`) and checkpoint revisions
  (FP8 `4e181f99…`, NVFP4 `b5c9332e…`) are the values any later run must match.
- "Private-reference scan scoped too narrowly" → run the committed scanner + document its
  `SCAN_ROOTS`; note the broad lexical/lockfile-URL scan is a recorded S8 human gate
  (S5 FA-3).
- "Risk register leaves a release blocker open without owner decision" → every
  release-blocking risk is Closed, Mitigated, or explicitly routed with an owner-visible
  disposition; the GPU-deferral is the owner's decision (this session).
- Failure modes: final docs must not contradict README/Docker; GPU-skipped must not read as
  GPU-supported; CPU-CI-green-locally must be qualified (GitHub runner unverified until push).
