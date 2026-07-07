# Session 6 Tasks - Local-Build Docker and Compose Migration

Session: MIG-S6
Derived from: `specs/*.md` (what) + `design.md` (how)

## 1. Context hygiene and env surface

- [ ] 1.1 Add root `.dockerignore` excluding `models/`, `.git`, `.venv`,
      `node_modules`, `.next`, `__pycache__`, `docs`, `references`, and all
      weight/media globs — spec `image_weight_and_path_safety` (D-9).
- [ ] 1.2 Add root `.env.example` documenting the `COSMOS3_*` checkpoint surface
      (from `docs/model_setup.md`) + deploy wiring vars (`API_INTERNAL_URL`,
      `COSMOS3_API_KEY`, `WEBUI_PORT`, `API_PORT`, per-stack checkpoint dirs) and the
      pinned repo ids/revisions — spec `external_checkpoint_mounts` (D-5).

## 2. WebUI image

- [ ] 2.1 Write `deploy/webui.Dockerfile` (multi-stage `node:22` → standalone runner)
      — spec `local_build_images` (D-2).
- [ ] 2.2 Verify: `docker build -f deploy/webui.Dockerfile -t cosmos3-nano-webui:local .`
      succeeds; runtime image launches `server.js`.

## 3. API image

- [ ] 3.1 Write `deploy/api.Dockerfile` (multi-stage; lean `python:3.12-slim` +
      Docker CLI default; `WITH_REASONING` ARG adds the CUDA+vLLM layer) — spec
      `local_build_images` (D-1).
- [ ] 3.2 Verify: `docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .`
      succeeds lean (torch-free; `docker` client present); the `WITH_REASONING` path
      is documented (build itself is S8).

## 4. vLLM-Omni image (render-only)

- [ ] 4.1 Write `deploy/vllm-omni.Dockerfile` FROM a CUDA 12.8 base, installing the
      immutable `MIG-S2` pin, serving the mounted checkpoint on `:8000`, readiness
      `/v1/models`, parameterized serve `command:` — specs `local_build_images`,
      `vllm_omni_pin_consumption` (D-3). Weight-copy-free.

## 5. Compose stacks

- [ ] 5.1 Write `deploy/docker-compose.base.yml` (`webui`+`api`+`vllm-omni`; wiring,
      ports, socket mount, gen-container `restart:"no"`, GPU reservation, inline
      `${VAR:-default}`) — specs `compose_stacks_and_render`,
      `external_checkpoint_mounts` (D-4/D-5/D-6/D-7/D-10).
- [ ] 5.2 Write `deploy/docker-compose.fp8.yml` and `deploy/docker-compose.nvfp4.yml`
      (`include:` base; override `COSMOS3_CHECKPOINT_LABEL` + checkpoint mount) — spec
      `compose_stacks_and_render`.
- [ ] 5.3 Write `deploy/docker-compose.reasoning.yml` overlay (api GPU + BF16 base
      mount + `COSMOS3_VLLM_BIN`) — spec `compose_stacks_and_render` (D-8).
- [ ] 5.4 Verify: `docker compose -f deploy/docker-compose.fp8.yml config` and
      `…nvfp4…` exit 0 with no unset-var warning; labels render `fp8`/`nvfp4`; wiring
      values render as specified; overlay renders on top of a stack.

## 6. Local operation commands

- [ ] 6.1 Write `Makefile` targets: `build`, `build-api`, `build-webui`,
      `config-fp8`, `config-nvfp4`, `up-fp8`, `up-nvfp4`, `down`, `health`, `smoke`,
      `scan` — spec `compose_stacks_and_render`.

## 7. Verification and review

- [ ] 7.1 Run all contract deterministic checks (render fp8+nvfp4, private-ref scan,
      weight-copy scan, `docker build` api+webui); classify any failure via the
      Failure Arbiter; save `docs/session_6/failure_arbiter.md` if any.
- [ ] 7.2 Sharded review (correctness / security / tests / architecture /
      performance); save `docs/session_6/sharded_review.md`; fix only High/Critical;
      re-check.
- [ ] 7.3 Adversarial verification (fresh context; contract + diff + evidence only);
      save `docs/session_6/adversarial_verification.md`.

## 8. Close

- [ ] 8.1 Update `docs/evidence_map.md`, `docs/risk_register.md` (R-06 + docker-socket
      row), `docs/eval_seed_cases.md`; add `docs/eval_corpus/mig_s6_*.md` seeds.
- [ ] 8.2 Amend `docs/session_6_contract.yaml` `allowed_files` only if needed
      (e.g. `docs/handoff.md`, `docs/eval_corpus/**`); flag for owner.
- [ ] 8.3 Verify the done condition (`GATE-MIG-S6-DOCKER`); write/update
      `docs/handoff.md` (Dockerfile paths, compose paths, env vars, vLLM-Omni pin,
      build/render results, manual GPU caveats); state remaining risks.

## Ordering / dependencies

1 (hygiene/env) precedes everything so builds have a clean context. 2 and 3 are
independent image builds. 4 is render-only. 5 depends on 1 (env) and references 2/3/4
service builds; 5.2 depends on 5.1; 5.3 composes with 5.1/5.2. 6 wraps 2–5. 7 runs
after 1–6 land. 8 closes after 7. Commit at clean checkpoints per task if requested.
