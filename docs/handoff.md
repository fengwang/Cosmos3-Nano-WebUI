# Session Handoff

## State Snapshot
- Session: **AM-S4** — Orchestration Simplification + Default-On (FP8). Risk high.
- Branch: `fea/eanble-reasoning-action-phase-5-session-4`.
- Last commit at start: `24ceef9` (reasoner build-context fix). This session's work is **uncommitted**
  (owner to review/commit, per the prior-session pattern).
- Current status: **GATE-AM-S4-ORCHESTRATION PASSES** — owner confirmed (Feng, 2026-07-26: tested all tabs/options on a fresh `make up-fp8`, all working, incl. the reasoning-400 fix).
  A single `make up-fp8` **cold-starts** and serves all three modes off the quantized-only FP8 checkpoint
  with correct on-demand residency swaps (never co-resident, ≤32 GiB); `t2i` non-regressed; zero BF16;
  CPU suite green; `openapi.json` unchanged. Sharded review + fresh-context adversarial verifier both
  **PASS**. The remaining gate is the owner's confirmation of the default `make up-fp8` all-modes run
  (routing §5 human gate; per-mode quality already PASSed in AM-S2/AM-S3).
- Changed files (this session):
  - **deploy/build**: `Makefile` (cold-start `up-fp8`/`up-nvfp4`; retire `up-fp8-reasoning` + `REASON`),
    `deploy/api.Dockerfile` (strip `WITH_REASONING` → lean torch-free image), **deleted**
    `deploy/docker-compose.reasoning.yml`, `.env.example` (drop BF16 env + base-download block).
  - **api**: `api/engines/vllm/coresidency.py` (R-08: FP8/KV footprint comment + `eviction` field
    `process_kill`→`container_stop`; no runtime-logic change).
  - **tests**: new `tests/deploy/{test_fp8_allmodes_wiring,test_no_legacy_overlay,test_reasoner_util_matches_contract}.py`;
    `tests/test_coresidency_unit.py` (eviction assertion updated to `container_stop`).
  - **docs**: `docs/session_4/**` (brainstorming, proposal, design, specs/, tasks, plan,
    execution_contract, sharded_review, adversarial_verification, evidence/P1);
    `docs/{model_setup,evidence_map,risk_register,eval_seed_cases,handoff}.md`.
- Checks run: `uv run pytest -m "not gpu"` = exit 0 (green, incl. `tests/deploy`); `tests/deploy` 11
  passed; `tests/test_coresidency_unit.py` green; `docker compose -f deploy/docker-compose.fp8.yml config`
  (raw + `--env-file .env`) = no BF16 mount, all-modes; nvfp4 `config` renders (exit 0);
  `rg "up-fp8-reasoning|WITH_REASONING|COSMOS3_BASE_DIR"` clean; `git diff --exit-code
  schemas/openapi.json` clean; **GPU-AM-ALLMODES-FP8** + **GPU-AM-T2I-NOREGRESS** (`evidence/P1`);
  sharded review + adversarial verifier (`docs/session_4/`).
- Checks NOT run: the **owner's** `make up-fp8` all-modes confirmation (human gate). NVFP4 all-modes
  (AM-S5). Multi-turn alternating Studio↔Action warmth (see the label follow-up below).

## Narrative Context
AM-S2/S3 already folded the reasoner container + action wiring into `docker-compose.base.yml`/`fp8.yml`
off the one FP8 checkpoint, and the orchestrator already owns container start/stop. The real AM-S4 work
was (1) a **latent boot co-load OOM** — `docker compose up -d` starts *every* service regardless of
`restart:"no"`, so a naive `make up-fp8` would boot omni (~14.7 GiB) **and** the reasoner (~26 GiB) at
once — fixed by cold-starting (`up -d --no-start` → `stop` heavy → `start api webui`) so the orchestrator
owns the heavy planes from a cold slot (zero orchestrator code change); (2) **deleting the legacy BF16
surface** (`docker-compose.reasoning.yml`, the `WITH_REASONING` build split, `up-fp8-reasoning`, BF16
env); (3) reconciling `docs/model_setup.md` + the `coresidency.py` footprint to zero-BF16; (4) the first
**full-stack** all-modes GPU smoke (api→orchestrator→container), which proved the GENERATION↔REASONING
evict-before-load swaps (never co-resident, peaks 13.5/26.1/13.9 GiB) and byte-identical t2i
non-regression.

## Decision Log
| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| Boot lifecycle | **Cold-start** (`up --no-start`+guard-stop+`start api webui`) | pre-warm generation; compose profiles; startup-eviction | zero orchestrator change; no boot co-load; owner picked cold-start | INV-5, design D1 |
| Cleanup depth | **Deploy-level delete** + minimal Python (coresidency comment/field) | deep removal of dead BF16-subprocess-reasoning Python | R-14 blast-radius-bleed; that code anchors the coresidency contract + belongs to AM-S2's serving path | design D4 |
| Fork pin | keep the reproducible COPY-patch; **defer** the public `fengwang/vllm` pin | pin now | needs the owner's git push; the COPY-patch already satisfies NFR-5 reproducibility-from-repo | NFR-5 |
| coresidency `eviction` field | **`container_stop`** (+ note the dormant subprocess path) | leave `process_kill` | prose said container-stop while the field said process_kill (adversarial F1); reconcile to the live reality | R-08 |
| Action label reload | **surface + defer** | fix the ResidencyId label now | pre-existing (AM-S3), out of approved AM-S4 scope, R-14; doesn't breach the gate | R-08, EV-AM-RESIDENCY-LABEL-CONSISTENCY |

## Next Priority Queue
1. **DONE ✅ — owner confirmed (Feng, 2026-07-26):** tested all tabs/options on a fresh `make up-fp8`
   (incl. the reasoning-400 fix); **`GATE-AM-S4-ORCHESTRATION` PASSES**. Evidence: `docs/session_4/evidence/P1`+`P2`.
2. **AM-S5 (NVFP4):** extend the unified FP8 all-modes design to NVFP4 (the template is the FP8
   compose/Makefile/orchestrator shape). NVFP4 currently has **no reasoner service** (Studio+Action only);
   a `/v1/reason` on nvfp4 errors honestly (no silent BF16). Add an nvfp4 reasoner + GPU-verify all three
   modes on the 4-bit Blackwell kernels; default-on only for modes that pass (INV-7).
3. **Follow-up — Studio+Action warm plane-merge (R-08):** align the t2i vs action `ResidencyId` label
   (t2i `None` vs action `'fp8'`) so alternating Studio↔Action does not reload omni. A focused,
   test-guarded change to the job→ResidencyId derivation (shared seam — do it deliberately, not at
   close-out). Seed: `EV-AM-RESIDENCY-LABEL-CONSISTENCY`.

## Warnings And Gotchas
- **Environment:** the owner's untracked repo-root `.env` pins `COSMOS3_FP8_DIR=/data/models/…`
  (absolute) and still carries stale `COSMOS3_BASE_DIR`/`COSMOS3_REASONER_MODEL_DIR`/`COSMOS3_VLLM_BIN`
  lines — **harmless** now (no compose file references them; the rendered config is BF16-free), but the
  owner may want to align `.env` to the trimmed `.env.example`. Confirm the resolved mount with
  `docker compose --env-file .env -f deploy/docker-compose.fp8.yml config` before trusting a run (R-11).
- **README stale ref (AM-S6):** `README.md` still says `make up-fp8-reasoning` (now deleted). README is
  forbidden this session (AM-S6 owns it) — AM-S6 MUST fix that reference and the per-mode status.
- **Deferred dead code (AM-S5+):** the BF16-subprocess-reasoning Python (`reasoning_spec`,
  `ReasonerConfig`, `server_launch_argv`, `build_reasoner`) stays — dead in the default (container) path,
  still anchoring the coresidency contract + edge tokenizer + ~5 tests. Remove in a focused later session.
- **Cold-start latency:** the first request of each mode after `make up-fp8` pays a one-time model load
  (~30–90 s); the 30-min idle keep-warm amortizes within a session. Expected, not a bug.
- **Known failing tests:** none.
- **Files future sessions must not casually edit:** `schemas/openapi.json` (INV-8); the proven
  `vllm-omni` image + `t2i` path (INV-2); `docs/archive/**`; `README.md`/`docs/walkthrough.md` (AM-S6).

## Eval Seeds
- Missed check (now caught): **EV-AM-COLD-START-NO-COLOAD** — `restart:"no"` does not gate `up -d` from
  starting; two heavy containers in one stack co-load unless bring-up leaves them created-but-stopped.
- New regression tests added: `tests/deploy/**` (zero-BF16 wiring, no-legacy-overlay, reasoner-util ==
  coresidency contract) — mutation-confirmed to have teeth.
- Instruction-update candidate: **EV-AM-RESIDENCY-LABEL-CONSISTENCY** — drive the REAL api→orchestrator
  surface (not a direct function call), so residency-identity mismatches (the t2i↔action reload) surface.
  Both recorded in `docs/eval_seed_cases.md` (AM-S4 harvest).

## AM-S4 amendment (2026-07-25): Reasoning HTTP 400 fix (owner-reported)
The owner hit **HTTP Error 400** from the WebUI Reasoning tab ("How chopsticks are made?"). Root cause: a
**context-cap drift** — the api's `ContextCapConfig` defaulted to 32768 while the `vllm-reasoner` serves
`--max-model-len 8192` (AM-S2), and the WebUI sends `/v1/reason` with no `max_output_tokens`, so the api
forwarded `max_tokens ≈ 32760` → the reasoner 400'd (relayed as "HTTP Error 400" in the WebUI). **Fix
(deploy/env, no code):** `deploy/docker-compose.fp8.yml` api env `COSMOS3_REASONER_MAX_CONTEXT=7680` +
`COSMOS3_REASONER_MAX_OUTPUT=7680` (8192 − 512 chat-template headroom). Reproduced → fixed (streams
coherent text); regression guard `tests/deploy/test_reasoner_context_cap_fits_model_len.py`; full CPU
suite + gates green. Evidence: `docs/session_4/evidence/P2-reasoning-400-fix.md`. **Extra changed files:**
`deploy/docker-compose.fp8.yml`, `tests/deploy/test_reasoner_context_cap_fits_model_len.py`. **AM-S5:**
set the analogous cap when it adds an nvfp4 reasoner + extend the guard test. **Future hardening:** the
api could discover the reasoner's `max_model_len` at runtime instead of a hardcoded env (kills the drift
class). Eval seed: `EV-AM-REASONER-CAP-MATCHES-MODEL-LEN`.
