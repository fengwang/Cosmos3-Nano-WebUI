# Session Handoff

## State Snapshot
- Session: `GPU-S1` — Public-Source vLLM-Omni Dockerfile Build
- Branch: `GPU-S1` (off `phase-2` at `b5e6598`)
- Last commit: `972bd5a` ("docs(gpu-s1): adversarial verification (PASS) + R-10 + layer-count fix")
- Changed files: `deploy/vllm-omni.Dockerfile`; deleted
  `deploy/docker-compose.local-image.yml`; `docs/release_checklist.md`,
  `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
  `docs/session_1_contract.yaml` (amended); full planning/evidence pack under
  `docs/session_1/**` (brainstorming, proposal, design, specs, tasks, plan,
  execution_contract, gate_record, failure_arbiter, sharded_review,
  adversarial_verification)
- Checks run: sm_120 CUDA-capability probe on `vllm/vllm-openai:v0.24.0`
  (live, RTX 5090); `docker compose build vllm-omni` (public inputs only,
  no cosmos3 prebuilt layer reuse); `up` + `/v1/models`; T2I generation on
  **both** FP8 and NVFP4 (exceeds the "at least one" bar), artifacts hashed
  and visually confirmed; base-layer provenance check against the forbidden
  `vllm/vllm-omni:cosmos3` prebuilt; 5-axis sharded review; fresh-context
  adversarial verification (independently reproduced the load-bearing
  claims from scratch). All re-runnable commands are in
  `docs/session_1/gate_record.md`.
- Checks not run: full `GPU-S3` joint validation (fresh `hf download` at
  `GPU-S2` revisions, full-stack through the `api`); a static CPU-only
  regression test guarding against this session's 3 historical Dockerfile
  bugs recurring (recommended, `tests/**` was outside this session's blast
  radius); the guardrails-on generation path completing end to end (blocked
  on gated model access / `HF_TOKEN`, tracked as `R-10`).
- Current status: **`GATE-GPU-S1-DOCKERFILE` PASSES**, adversarially
  verified. Session complete.

## Narrative Context

`deploy/vllm-omni.Dockerfile` was rebuilt from `vllm/vllm-openai:v0.24.0`
(the fork's own base image tag, empirically confirmed sm_120-capable) with
the fork installed by immutable commit SHA via `uv pip install`, and the
serve entrypoint fixed to the confirmed `vllm serve --omni` command with
`ENTRYPOINT []` cleared (the base image's own `ENTRYPOINT ["vllm","serve"]`
was silently doubling the command — the first real bug hit). Five issues
surfaced and were fixed or classified during implementation (see
`docs/session_1/failure_arbiter.md` FA-1..FA-6): a missing `uv --system`
flag, a version-detection bug in the external fork's own build backend, the
entrypoint doubling, a `--env-file .env` invocation gap, an expected
guardrails-on-by-default crash without gated model access, and — caught
only by the sharded review, not by implementation — a drafting gap in this
session's own contract that omitted `docs/handoff.md`/`docs/eval_seed_cases.md`
from its blast radius (amended as `GPU-S1-A1` with owner sign-off before
writing this file). Both FP8 and NVFP4 generate real, verified T2I
artifacts on the RTX 5090 through the rebuilt image. The
`docker-compose.local-image.yml` stopgap is deleted per the owner's explicit
choice (not kept as a documented convenience).

## Decision Log

| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| Execution mode | Full live execution (real Docker/GPU/network in-session) | Prepare-only; hybrid probe-then-gate | Real hardware was available and the contract's own checks are literal build/serve commands | `session_1_contract.yaml` deterministic_checks |
| Base image | `vllm/vllm-openai:v0.24.0` (matches fork exactly) | Already-cached `latest`/v0.21.0 | Least likely to hit a vLLM-internals/vllm-omni version mismatch; pull turned out near-free (shared layers) | PRD §3 Owner Decisions; `docs/session_1/design.md` Decision 1 |
| Fork install mechanism | Single-line `uv pip install git+https://…@<sha>` | Explicit `git clone` + `checkout` + `uv pip install .` | Smaller diff, equivalent to the fork's own pattern adapted for a consumer repo | `docs/session_1/design.md` Decision 2 |
| `docker-compose.local-image.yml` disposition | Delete entirely | Keep as documented "reuse a prebuilt image" convenience | Owner's explicit choice, overriding the initial recommendation | PRD Owner Decision 8; `docs/session_1/specs/local-image-override-disposition.md` |
| Checkpoint coverage for T2I smoke | Both FP8 and NVFP4 | FP8 only (contract's minimum) | Both already unpacked locally with the workaround pre-applied; retires the FP8/NVFP4-asymmetry adversarial case outright | `session_1_contract.yaml` adversarial_cases |
| Guardrails default in shipped `CMD` | On (not baked `--no-guardrails`) | Bake `--no-guardrails` into the default | Safer default; license-compliance-sensitive; `--no-guardrails` used only as an explicit, documented override for this session's own smoke test | `docs/session_1/specs/vllm-omni-serve-entrypoint.md` |
| Commit cadence | Commit at each clean task checkpoint | Stage only, let owner commit | Matches this repo's demonstrated per-checkpoint convention across every prior session | Owner decision, `docs/session_1/brainstorming.md` |
| `docs/handoff.md`/`docs/eval_seed_cases.md` blast-radius gap | Amend `session_1_contract.yaml` (`GPU-S1-A1`) | Proceed anyway; redirect into `docs/session_1/**` only | Fixes the drafting oversight for good, matches sibling-contract precedent, preserves the canonical top-level pattern future sessions rely on | `docs/session_1/failure_arbiter.md` FA-6; `docs/session_1/sharded_review.md` F1 |

## Next Priority Queue
1. **`GPU-S2`** (checkpoint fix and re-pin sweep) — the natural next session per the PRD's session plan; independent of anything left open here.
2. **`R-10`** — provision gated `nvidia/Cosmos-1.0-Guardrail` model access / `HF_TOKEN` in a GPU-capable session and re-run the T2I smoke with guardrails on, to close the one path this session never proved working end to end.
3. Consider (not this session's authority — `tests/**` was out of blast radius): a cheap, CPU-only static regression test guarding against `--break-system-packages`, the old wrong CMD string, or `--no-guardrails` creeping back into `deploy/vllm-omni.Dockerfile`, following the precedent of `tests/test_private_ref_scan.py`.
4. When drafting `GPU-S4`/`GPU-S5`'s own execution against their contracts, double-check their `blast_radius.allowed_files` includes `docs/handoff.md`/`docs/eval_seed_cases.md` up front (a quick grep), rather than discovering the gap mid-session the way `GPU-S1` did.

## Warnings And Gotchas
- **Environment issues:** `docker compose` invoked from the repo root against `deploy/docker-compose*.yml` needs `--env-file .env` explicitly — Compose's project directory defaults to `deploy/`, so a repo-root `.env` is silently ignored otherwise, and Docker auto-creates an empty directory for the resulting missing bind-mount source rather than erroring (see FA-4). The `Makefile`'s targets already handle this (`ENV_FILE := $(wildcard .env)`); prefer them or replicate the flag when invoking `docker compose` directly.
- **`deploy/docker-compose.base.yml` does not publish the `vllm-omni` service's port to the host** by design (the `api` service owns its lifecycle and is the intended consumer, over the Compose bridge network). Verify `/v1/models` via `docker exec <container> curl ...` or from a peer container on the same network, not a bare host-side `curl localhost:8000` — and note the sharded review (F6) flagged that the loopback check only proves server-process health, not cross-container bridge reachability; `GPU-S3` should independently confirm the `api`→`vllm-omni` path.
- **Known failing checks:** the session contract's literal `deterministic_checks` text (`up -d` + `curl localhost:8000/v1/models`, no other flags) does not pass as written — it needs both `--env-file .env` and an explicit `--no-guardrails` override to get a serving container. This is disclosed in depth in `docs/session_1/gate_record.md`'s dedicated re-run section, not a hidden gap.
- **Deferred risks:** `R-10` (guardrails-on generation path unverified, gated-access-blocked). `R-02`/`R-03`/`R-04` (checkpoint fix risks) are `GPU-S2`'s to carry, unaffected by this session.
- **Files future sessions must not casually edit:** `docs/archive/phase-1/**` (never edited post-archive); any `wfen/*` Hugging Face repo content (external, requires an explicit owner go-ahead per NFR-3); `deploy/vllm-omni.Dockerfile`'s fork-install pin (`697035018b70cef76b974a909d23371a9984c3f2`) — changing it requires the same whole-repo re-pin sweep discipline as a checkpoint revision change (`project_contract.md` §6).

## Eval Seeds
- Missed check: the layer-hash cosmos3-reuse check has a `COPY --from=` blind spot — added as `EV-GPU-DOCKERFILE-NO-COSMOS3-TEXTUAL` in `docs/eval_seed_cases.md`.
- New regression test candidate: `EV-GPU-DOCKERFILE-GUARDRAILS-DEFAULT` (added) — confirm the shipped `CMD` fails closed, not open, without gated guardrail access.
- Instruction update candidate: when drafting a new `GPU-S#` (or any) session contract from a template, explicitly checklist `docs/handoff.md` and `docs/eval_seed_cases.md` into `blast_radius.allowed_files` — this was the one drafting gap this session's own contract had relative to every sibling contract.
