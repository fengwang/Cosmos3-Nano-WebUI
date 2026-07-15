# GPU-S1 Tasks — Public-Source vLLM-Omni Dockerfile Build

Input: `docs/session_1/design.md`, `docs/session_1/specs/*.md`

## 1. Pre-Flight Verification

- [ ] 1.1 Re-confirm GPU is idle and Docker/network baseline still holds
      immediately before building (state may have changed since
      brainstorming).
- [ ] 1.2 Pull `vllm/vllm-openai:v0.24.0` and rerun the sm_120 CUDA
      capability probe (same probe already run successfully against
      `latest`). This is the contract's named human gate: stop and report
      if this fails, rather than silently picking a different base image.

## 2. Dockerfile Rework

- [ ] 2.1 Rewrite `deploy/vllm-omni.Dockerfile`: base image
      `vllm/vllm-openai:v0.24.0`, fork install via `uv pip install
      "git+https://github.com/fengwang/vllm-omni.git@697035…"` (fallback to
      plain `pip install --no-cache-dir` if `uv` is absent), `CMD` fixed to
      the confirmed `vllm serve --omni` entrypoint with `--init-timeout
      1800` and no `--no-guardrails`.
- [ ] 2.2 `docker compose -f deploy/docker-compose.fp8.yml build vllm-omni`
      — iterate until it exits 0. Record base image tag, build command,
      and duration.
- [ ] 2.3 Verify no `vllm/vllm-omni:cosmos3` layer leaked into the new image
      (`docker history` / base-layer ID comparison).

## 3. Serve + T2I Verification (depends on 2)

- [ ] 3.1 `docker compose -f deploy/docker-compose.fp8.yml up -d vllm-omni`
      and `curl -sf http://localhost:8000/v1/models` → HTTP 200.
- [ ] 3.2 Send an FP8 T2I request; capture the request, response, exit
      code, and artifact metadata as evidence.
- [ ] 3.3 Tear down, then bring the NVFP4 stack up
      (`docker-compose.nvfp4.yml`) against the same built image; confirm
      `/v1/models` again.
- [ ] 3.4 Send an NVFP4 T2I request; capture the same evidence fields.
- [ ] 3.5 Tear down containers cleanly (`docker compose down`).

## 4. Local-Image Stopgap Disposition

- [ ] 4.1 Delete `deploy/docker-compose.local-image.yml`.
- [ ] 4.2 Record the removal decision and reason in `release_checklist.md`
      and `evidence_map.md` (per
      `docs/session_1/specs/local-image-override-disposition.md`).

## 5. Documentation Sync (depends on 2, 3, 4)

- [ ] 5.1 Update `docs/release_checklist.md` §6 with the new build/serve/T2I
      evidence, flipping the relevant `[ ]` items to `[x]`.
- [ ] 5.2 Add fresh evidence rows to `docs/evidence_map.md` (build result,
      sm_120 confirmation, T2I FP8/NVFP4 results, local-image disposition).
- [ ] 5.3 Update `docs/risk_register.md`: close/advance R-01 (base image
      sm_120 support) and R-09 (GPU host availability) with this session's
      evidence.

## 6. Review and Verification (risk = high → mandatory)

- [ ] 6.1 Run sharded review across correctness, security, tests,
      architecture, and performance axes.
- [ ] 6.2 Fix High/Critical findings only; re-run the targeted checks they
      affect.
- [ ] 6.3 Run adversarial verification with a fresh-context reviewer that
      sees only the contract, diff, and evidence.
- [ ] 6.4 If any check fails the same way twice, invoke the Failure Arbiter
      before attempting another fix.

## 7. Session Close

- [ ] 7.1 Re-run the full deterministic check list from
      `session_1_contract.yaml`.
- [ ] 7.2 Verify `GATE-GPU-S1-DOCKERFILE`'s done condition against the
      recorded evidence.
- [ ] 7.3 Write/update `docs/handoff.md`.
- [ ] 7.4 Add eval seeds to `docs/eval_corpus/` for anything caught or
      missed this session.
- [ ] 7.5 State remaining risks and warnings for `GPU-S2`/`GPU-S3`.
