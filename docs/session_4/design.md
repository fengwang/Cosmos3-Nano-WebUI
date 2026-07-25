# AM-S4 Design — Orchestration Simplification + Default-On (FP8)

Date: 2026-07-25
Status: approved (owner, 2026-07-25). Consumes `brainstorming.md` + `proposal.md`.

## Context

- The orchestrator is a single-slot residency FSM: one mutable `ResidencyId` behind an
  `asyncio.Lock`; `plan_acquire` decides evict-before-load; eviction frees VRAM
  (container **stop** for `ContainerPlaneWorker`, process-kill for
  `SubprocessPlaneWorker`); a post-evict VRAM gate refuses the next load until VRAM
  drops (`manager.py:65-91`, `residency.py:35-46`, `container.py:97-106`).
- Generation (Studio) + Action share one resident `vllm-omni` container on
  `Plane.GENERATION` (~14.3–14.7 GiB peak). Reasoning is a separate `vllm-reasoner`
  container on `Plane.REASONING` (~26 GiB, KV-cache-dominated at 0.85 util). They must
  never co-reside in the 32 GiB budget (INV-5).
- Both heavy services declare `restart: "no"` and are controlled by the api via
  `DockerCliController` (`docker start|stop <fixed-name>`, docker.sock mounted).
- **Gap:** `docker compose up -d` starts *every* service regardless of `restart:
  "no"`, so `make up-fp8` would boot both heavy containers → co-load OOM. The
  orchestrator starts cold and never stops compose-started containers.

## Goals

1. One `make up-fp8` serves Studio + Reasoning + Action off the quantized-only FP8
   checkpoint, with the orchestrator swapping residency and never co-loading.
2. Default path has no BF16 base mount, no reasoning overlay, no `WITH_REASONING`
   build (INV-4), verifiable by `docker compose … config` + a deterministic test.
3. `docs/model_setup.md` requires only the quantized checkpoint(s) for all modes.
4. `t2i` non-regressed (INV-2); CPU suite green; API shape unchanged (INV-8).

## Non-Goals

NVFP4 GPU-verify + nvfp4 reasoner service (AM-S5); README/walkthrough (AM-S6); deep
removal of the dead BF16-subprocess-reasoning Python; public `fengwang/vllm` fork pin;
any `diffusers` `t2v`; auth/guardrails/network; webui changes (unless the smoke
surfaces a real bug, R-12).

## Decisions

- **D1 — Cold-start via `up --no-start` + guard-stop + start-light (not profiles, not
  startup-eviction).** Rationale: requires **zero** orchestrator change — the cold-slot
  FSM already loads on first request and evict-before-loads on swap; profiles break
  `docker start` (services not created); startup-eviction leaves a boot-time co-load
  race. The idempotent `stop vllm-omni vllm-reasoner` guard guarantees cold heavy
  planes even on a re-run that left one running. First-request cold-load latency is
  accepted (idle keep-warm amortizes).
- **D2 — Delete, don't demote, the legacy BF16 surface.** The AM-S2 FP8 reasoner
  container fully supersedes the BF16 subprocess overlay; honors the session's
  no-backward-compat rule + zero-BF16 posture. Verified no test references the deleted
  deploy artifacts.
- **D3 — api image becomes lean/torch-free unconditionally.** Reasoning is a container;
  the api never needs torch/vLLM. Removing the `WITH_REASONING` build variant is a net
  simplification (no CUDA base, faster/lighter api image).
- **D4 — Keep the deep dead subprocess-reasoning Python; reconcile only the coresidency
  footprint comment.** `ReasonerConfig`/`server_launch_argv`/`build_reasoner`/
  `reasoning_spec` anchor the coresidency VRAM contract + edge tokenizer and belong to
  AM-S2's serving path; ~5 test files depend on them. Removing them now is
  blast-radius bleed (R-14) into another session's domain. Deferred with an explicit
  handoff note. The `0.85` util constant is kept because it matches the live compose
  reasoner command; a new test asserts that equality so the contract can't silently
  drift from runtime.
- **D5 — Mirror cold-start to `up-nvfp4` for consistency.** nvfp4 is omni-only (no
  reasoner service yet), so cold-start is strictly safe there; it also pre-positions
  AM-S5. Not GPU-verified here (contract: keep nvfp4 renderable only).
- **D6 — nvfp4 reasoning errors honestly.** `base.yml` sets a reasoner URL/container
  default, but nvfp4 has no reasoner service, so a `/v1/reason` on nvfp4 fails at
  `docker start` (no such container) rather than silently falling back to BF16
  (INV-4/INV-7). Documented for AM-S5.

Alternatives considered: pre-warm generation at boot (rejected — needs orchestrator
startup-reconciliation + a new failure surface; owner chose cold-start); deep code
clean (rejected for AM-S4 — R-14).

## Risks / Trade-offs

- [First-request cold-load latency ~30–90 s] → accepted; 30-min idle keep-warm amortizes.
- [`up --no-start` leaves a previously-running heavy container up] → idempotent
  `stop vllm-omni vllm-reasoner` guard neutralizes it every bring-up.
- [`up --no-start` might not build a missing `:local` image] → the GPU smoke's first
  step is a clean `make down && make up-fp8`; if a build is skipped, `make build`
  precedes it (verified during the smoke). Deterministic tests don't depend on a build.
- [Config↔runtime drift: docs say "no overlay" but runtime still needs it] → closed:
  the reasoner is a first-class compose service (not an overlay) and the wiring test
  asserts no BF16 mount + reasoner-util == contract.
- [Stale coresidency footprint misleads a future reader (R-08)] → comment updated to
  the FP8/KV-dominated reality.
- [Deep dead BF16-subprocess-reasoning code remains] → deferred, documented (not
  hidden) in handoff; it is unreachable in the default path (container path only).
- [nvfp4 reasoning errors until AM-S5] → honest failure, no silent BF16.

## Migration Plan

1. Land deploy + Makefile + `.env.example` + `api.Dockerfile` changes; delete
   `docker-compose.reasoning.yml`.
2. Add `tests/deploy/` wiring tests; update `coresidency.py` comment.
3. Reconcile `docs/model_setup.md`.
4. CPU suite + deterministic gates green (host-runnable).
5. Sharded review + adversarial verifier (risk=high); fix High/Critical only.
6. GPU all-modes smoke (agent-driven) + owner confirmation → `GATE-AM-S4-ORCHESTRATION`.
7. Handoff + eval seeds + evidence/risk updates.

**Rollback:** all changes are on the session branch; `git revert`/branch-drop restores
the prior three-posture layout. No checkpoint re-export, no schema change, no weight
mutation — rollback is purely source-level.

## Open Questions

None blocking. Deferred (owner-acknowledged): public fork pin timing (AM-S5/NFR-5);
deep dead-code removal (AM-S5); nvfp4 reasoner service (AM-S5).
