# Session 6 Execution Contract - Local-Build Docker and Compose Migration

Session: MIG-S6
Risk: high · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S6-DOCKER`

## Planned file changes

Created:
- `deploy/webui.Dockerfile`, `deploy/api.Dockerfile`, `deploy/vllm-omni.Dockerfile`
- `deploy/docker-compose.base.yml`, `deploy/docker-compose.fp8.yml`,
  `deploy/docker-compose.nvfp4.yml`, `deploy/docker-compose.reasoning.yml`
- `.dockerignore`, `.env.example`, `Makefile`
- `docs/session_6/{brainstorming,proposal,design,tasks,plan,execution_contract}.md`,
  `docs/session_6/specs/{local_build_images,compose_stacks_and_render,
  external_checkpoint_mounts,vllm_omni_pin_consumption,image_weight_and_path_safety}.md`
- `docs/session_6/{failure_arbiter (if any),sharded_review,adversarial_verification}.md`
- `docs/eval_corpus/mig_s6_*.md`

Updated:
- `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
  `docs/handoff.md`
- `docs/session_6_contract.yaml` (`allowed_files` amendment — see below; owner review)

## Allowed blast radius

Permitted (contract `allowed_files`): `deploy/**`, `.dockerignore`, `Dockerfile`,
`docker-compose*.yml`, `Makefile`, `.env.example`, `docs/session_6/**`,
`docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`.

Amendment requested (owner review, mirrors S4 FA-4 / S5 D10 precedent): add
`docs/handoff.md`, `docs/eval_corpus/**`, and `docs/session_6_contract.yaml` to
`allowed_files` — the Session End Protocol requires writing the handoff and eval
seeds, which the literal list omits. Running (not editing) `tests/test_private_ref_scan.py`
is in-bounds.

Forbidden (stop if a change seems required): model-weight/media files; Docker
**publishing** workflows; GitHub secrets; `README.md`; vLLM-Omni fork source (consumed
by pinned install only, never vendored/submoduled); any `api/**` or `webui/**` product
code (honored as-imported — INV-9 preserved by construction). No new repo production
dependency (INV-10); images install pinned public artifacts at build time only.

## First test to write

The FP8 render check, run **before** any compose file exists (spec
`compose_stacks_and_render`):
```bash
docker compose -f deploy/docker-compose.fp8.yml config    # baseline: FAILS (no such file)
```
It must fail for "no configuration file / no such file" at baseline, then — after
Tasks 1 and 5 — exit 0 with `COSMOS3_CHECKPOINT_LABEL: fp8`, the three services, and
no unset-variable warning. The weight-copy scan is the second always-on assertion:
```bash
rg -n "COPY .*\.(safetensors|pt|pth|ckpt)|ADD .*\.(safetensors|pt|pth|ckpt)" deploy   # must stay empty
```

## Checks to run after each task

- Render (contract): `docker compose -f deploy/docker-compose.fp8.yml config` and
  `…nvfp4…` → exit 0, correct label, no unset-var warning; overlay renders on a stack.
- Weight-copy scan: `rg -n "COPY .*\.(safetensors|pt|pth|ckpt)|ADD .*\.(...)" deploy`
  → empty.
- Private-reference scan: `uv run python tests/test_private_ref_scan.py` → 0 findings;
  `rg -n "$PRIVATE_REF_PATTERN" deploy docs/session_6 .env.example` and a `/home/`
  spot-check → empty (`$PRIVATE_REF_PATTERN` unset → S1 baseline, ENVIRONMENT).
- Image builds: `docker build -f deploy/webui.Dockerfile -t cosmos3-nano-webui:local .`
  and `docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .` → success
  (api lean; `docker` client present). vLLM-Omni build NOT run (S8 gate).
- Wiring assertions from the rendered config: `API_INTERNAL_URL=http://api:8000`,
  `COSMOS3_VLLM_OMNI_URL=http://vllm-omni:8000`,
  `COSMOS3_GEN_CONTAINER=cosmos3-nano-webui-vllm-omni`,
  `container_name: cosmos3-nano-webui-vllm-omni`, docker.sock mount, `restart:"no"`.

## Review axes to run at the end

correctness · security · tests · architecture · performance (per
`docs/agent_workflow/prompts/sharded_review.md`). Each reviewer read-only; reports
severity + evidence (file/line) + violated clause + smallest safe fix + confidence.
Fix only High/Critical; re-run checks after fixes.

## Adversarial verifier brief

Fresh context; sees only `docs/session_6_contract.yaml`, the session diff, and the
evidence — not this conversation. Task: falsify "`GATE-MIG-S6-DOCKER` passes with
local-build Compose ready for README documentation." Specifically attempt to show the
contract's adversarial cases: (a) a Dockerfile copies weights through a broad `COPY .`
or a weight glob; (b) Compose renders but points at a private/absolute default path;
(c) the vLLM-Omni pin is mutable or branch-only (not the immutable tag/commit); (d) the
api/webui containers can only run on a private-network setup; plus (e) a private path/
host/secret leaked into any `deploy/**` or session doc; (f) the FP8/NVFP4 render emits
an unset-variable warning or fails; (g) an image bakes a checkpoint or a new repo
dependency was added (INV-2/INV-10). Any confirmed item fails the session and is routed
through the Failure Arbiter.

## Concrete done condition

`GATE-MIG-S6-DOCKER` is satisfied when all hold, each backed by command evidence:
1. `docker compose -f deploy/docker-compose.fp8.yml config` and `…nvfp4…` exit 0 with
   the correct label and no unset-variable warning; the reasoning overlay renders on
   top of a stack.
2. The rendered config wires `webui`→`http://api:8000`, `api`→`http://vllm-omni:8000`
   + container `cosmos3-nano-webui-vllm-omni`, mounts the docker socket, and gives the
   generation container `restart:"no"` with orchestrator-owned lifecycle.
3. Checkpoints are external, env-configurable, repo-relative `./models/<Repo>`
   defaults — no baked weights, no private/absolute default path.
4. `deploy/vllm-omni.Dockerfile` installs the immutable `MIG-S2` tag/commit; no
   submodule/vendored fork is added.
5. Weight-copy and private-reference scans over `deploy/`, `.env.example`, and
   `docs/session_6/**` are clean.
6. `docker build` succeeds for the lean api and the webui images (vLLM-Omni build +
   all GPU inference explicitly deferred to `MIG-S8`, with commands recorded).
7. `Makefile` exposes build/up/down/health/smoke/scan.
8. Sharded review has no unresolved High/Critical; adversarial verifier passes.
9. `docs/handoff.md` hands S7/S8 the Dockerfile paths, compose paths, env vars, the
   vLLM-Omni pin, build/render results, and the manual GPU caveats.
