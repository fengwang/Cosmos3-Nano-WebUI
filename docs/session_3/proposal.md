# Session 3 Proposal - Joint Validation on RTX 5090

Date: 2026-07-09

## Motivation

`GPU-S1` proved the from-source Dockerfile builds and serves T2I, but against
the *pre-fix* checkpoint with a manual workaround. `GPU-S2` proved the
checkpoints themselves resolve cleanly from a fresh clone/download, but never
ran them through the from-source image. Neither session proves the combined,
publicly-reproducible claim: a fresh operator following only the README, with
a fresh `hf download` at the new revisions and the from-source image, gets a
working, no-workaround T2I deployment. `docs/session_3.md` exists to close
that joint gap and retire archived risk R-13's "proxy image, not
pinned-commit build" caveat for good, plus attempt a best-effort T2V smoke
(PRD FR-6, SHOULD).

## Agreed Changes (from brainstorming)

- Run the full joint-validation pipeline live against real hardware in this
  session (not just plan it) — the environment probes in
  `docs/session_3/brainstorming.md` confirmed this is feasible and matches
  `GPU-S1`/`GPU-S2` precedent.
- R-10 (guardrails-on path) is **out of scope**; this session runs with
  `--no-guardrails`, same as `GPU-S1`.
- Verification tooling is a set of small, independently-runnable probes (one
  per task) plus a pure aggregator, not one monolithic script and not a
  shell-only runbook.
- T2I evidence for both checkpoints, both direct and full-stack, is fully
  recorded before the T2V smoke is attempted.
- T2V smoke is direct-only, attempted on NVFP4 first (VRAM headroom), with a
  scoped-out reason recorded if neither checkpoint fits.

## Capabilities

### New Capabilities

- **`gpu-validation-probes`** — probes that fetch the fresh checkpoints and
  drive direct and full-stack T2I generation for FP8 and NVFP4 against the
  `GPU-S1` image, each producing a structured evidence fragment.
- **`t2v-smoke-verification`** — a best-effort, direct-only T2V probe with a
  tri-state outcome (pass / fail / explicitly-scoped-out), never blocking on
  failure.
- **`evidence-aggregation`** — a pure merge of every probe's evidence
  fragment into one `probes/evidence.json` and a human-readable
  `probes/summary.md`.

### Modified Capabilities

- **`per-mode-verification-status-reporting`** — the per-mode markings in
  `README.md`, `docs/model_setup.md` §6/§8, and `docs/release_checklist.md`
  §7 currently read "GPU-unverified" for every generation mode. This session
  changes that requirement: FP8 and NVFP4 `t2i` upgrade to "T2I-verified"
  wherever the new evidence supports it; every other mode's marking is
  unchanged (out of scope, not touched).
- **`risk-and-eval-case-closure`** — `docs/risk_register.md` rows R-05 and
  R-09, and `docs/eval_seed_cases.md` rows `EV-GPU-FP8-T2I`,
  `EV-GPU-NVFP4-T2I`, `EV-GPU-T2V-SMOKE`, `EV-GPU-JOBS-ARTIFACT`, currently
  read "Open - blueprint-time" / undefined result. This session changes that
  requirement: each row closes with a recorded evidence-backed result (pass,
  fail, or explicitly scoped out), never left silently open without a
  reason.

## Impact

- **Affected docs (allowed blast radius):** `docs/session_3/**` (new),
  `docs/model_setup.md`, `docs/release_checklist.md`, `README.md`,
  `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
  `docs/handoff.md`.
- **Affected runtime surfaces:** none. No change to `api/**`, `webui/**`,
  `deploy/vllm-omni.Dockerfile`, or `schemas/**` — this session only
  *consumes* `GPU-S1`'s image and `GPU-S2`'s checkpoints.
- **Affected external systems:** a genuinely fresh `hf download` of both
  `wfen/*` repos (read-only) and local Docker Compose lifecycle for
  `deploy/docker-compose.fp8.yml` / `.nvfp4.yml`. No push to any external
  repo.
- **New local artifacts (not committed as bulky data):** `models/` checkpoint
  directories at repo root (already gitignored as external weights per
  `docs/model_setup.md` §3 / INV-2) and `docs/session_3/probes/evidence*.json`
  + `summary.md` (small, structured, committed as evidence).
