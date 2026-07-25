# P1 — Full all-modes GPU smoke (FP8), one `make up-fp8`

Date: 2026-07-25 · Session AM-S4 · RTX 5090 (sm_120), 32607 MiB, driver 610.43.03.
Checkpoint: `/data/models/Cosmos3-Nano-FP8-Blockwise` (deployed rev `4e181f9`, quantized-only,
resolved via `--env-file .env`; `config` shows only this checkpoint — **no BF16 mount**).
Images: `cosmos3-nano-api:local` (rebuilt lean/torch-free from the AM-S4 Dockerfile),
`cosmos3-nano-vllm-omni:local`, `cosmos3-nano-vllm-reasoner:local`, `cosmos3-nano-webui:local`.

This is the **first full-stack** api→orchestrator→container smoke (P3/AM-S2 named it the AM-S4
candidate): every request goes through the api HTTP surface, so the **orchestrator** performs the
docker start/stop + evict-before-load swaps.

## Cold start (the AM-S4 deliverable)

`make down && make build-api && make up-fp8` → only `deploy-api-1` + `deploy-webui-1` running;
`cosmos3-nano-webui-vllm-omni` + `cosmos3-nano-webui-vllm-reasoner` in **Created (not started)**;
GPU **18 MiB** (nothing pre-loaded); `GET /v1/health/ready` → `{"status":"ready"}`. **No boot
co-load** — the pre-AM-S4 hazard (`up -d` starting both heavy containers) is closed.

## All-modes sequence (VRAM sampled live; orchestrator logs quoted)

| Step | Request (api) | Orchestrator decision (from `cosmos3.orchestrator` logs) | Result | Peak VRAM | co-resident? |
|---|---|---|---|---|---|
| 1 Studio | `POST /v1/jobs {mode:t2i,480×480}` | cold → **load GENERATION** (docker start omni) | `succeeded`, PNG **691,968 B** (magic `89504e47`) | 13,488 MiB | no |
| 2 Reason | `POST /v1/reason` | **evict GENERATION → load REASONING** (`20:22:53`) | coherent SSE text¹ | 26,124 MiB | **no** (omni→0 before reasoner→1, VRAM 13420→18→…→26124) |
| 3 Studio | `POST /v1/jobs {mode:t2i}` | **evict REASONING → load GENERATION** (`20:26:04`) | `succeeded`, PNG **691,968 B** | 13,488 MiB | **no** (reasoner→0 @ 26124→18 before omni→1) |
| 4 Action | `POST /v1/action/policy` (agibotworld, shipped asset) | evict `GENERATION(None)` → load `GENERATION('fp8')` (`20:28:04`) | `succeeded`, MP4 **629,416 B** (ftyp) + `[16,29]` trajectory | 13,856 MiB | no |

¹ *"…the lack of friction between the gripper and the cup's surface reduces the grip strength
needed to hold it securely."* — coherent reasoning off the quantized FP8 reasoner.

`co_load_ever=0` was asserted in every monitored step (omni and reasoner **never** both running).
All peaks ≤ 32 GiB. Clean teardown: `make down` → GPU **18 MiB**, all containers removed (no leak).

## Gate mapping (GATE-AM-S4-ORCHESTRATION)

- **All three modes on one `make up-fp8`** — Studio ✓, Reasoning ✓, Action ✓.
- **Correct on-demand swaps** — GENERATION↔REASONING evict-before-load, both directions, logged ✓.
- **INV-5 residency safety net** — never co-resident; peaks 13.5 / 26.1 / 13.9 GiB ≤ 32 ✓.
- **INV-2 t2i non-regressed** — 691,968-byte PNG **byte-size-identical** to the P3/AM-S2 baseline,
  before **and** after the reasoning swap ✓.
- **INV-4 zero-BF16** — resolved `config` mounts only the FP8 checkpoint; no BF16 base ✓.
- **INV-8** — no `schemas/openapi.json` change; the smoke used only existing endpoints ✓.
- **Owner confirmation** — the human gate (routing §5) is **pending** (owner to confirm the
  default `make up-fp8` all-modes run; per-mode quality already PASSed in AM-S2/AM-S3).

## Finding surfaced by the full-stack smoke (pre-existing; not an AM-S4 regression)

Step 4 shows t2i acquires `ResidencyId(GENERATION, label=None)` while action acquires
`ResidencyId(GENERATION, label='fp8')`. Because the labels differ, the FSM evicts+reloads omni when
**alternating t2i↔action**, even though both are the same GENERATION plane / same container / same
checkpoint. This does **not** breach the gate (evict-before-load held, never co-resident, ≤32 GiB),
but it means AM-S3's "Studio+Action plane-merge = *no swap*" holds only as "same plane" — a
label-driven reload occurs on alternation. My AM-S4 diff never touches label derivation (Makefile /
deploy / docs / comments only), so this is a **pre-existing** inconsistency the full-stack path
newly reveals; AM-S3's `vllm_omni_work` direct-call could not surface it. Recorded as an eval seed +
a focused follow-up (align the two paths' ResidencyId label so Studio+Action truly share warm). See
`docs/risk_register.md` R-08 note and `docs/handoff.md`.
