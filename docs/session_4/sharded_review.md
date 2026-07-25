# AM-S4 Sharded Review

Date: 2026-07-25. Risk: high → 6-axis sharded review over the uncommitted diff, run by
three independent read-only reviewers. Protocol:
`docs/agent_workflow/prompts/sharded_review.md`.

## Diff under review

Makefile (cold-start `up-fp8`/`up-nvfp4`, retire `up-fp8-reasoning`); delete
`deploy/docker-compose.reasoning.yml`; `deploy/api.Dockerfile` (strip `WITH_REASONING`
→ lean torch-free); `.env.example` (drop BF16 env); `api/engines/vllm/coresidency.py`
(R-08 comment only); `docs/model_setup.md` (zero-BF16 reconciliation); new
`tests/deploy/**`; `docs/session_4/**`.

## Reviewer verdicts

- **Correctness + Architecture — PASS, no findings.** Confirmed: the cold-start recipe
  (`up -d --no-start` → `stop` heavy → `start api webui`) leaves both heavy planes
  stopped in all states; the orchestrator legitimately needs no change (cold slot →
  `docker start` on first request → evict-before-load on swap); no top-level torch/vLLM
  import breaks the lean api image; blast radius clean (no forbidden file); INV-4/5/7/8
  hold; API shape unchanged.
- **Security + Performance — PASS.** No secrets/weights/private paths (INV-1); docker.sock
  surface unchanged; fixed (non-request) container names; no dangling references to the
  deleted overlay (repo-wide grep clean); cold-start latency acceptable + documented;
  no container accumulation (fixed names reused); `make down` frees both stacks. Two
  Low/Nit doc-clarity notes.
- **Tests + Readability — 4 High + 2 Medium, all test robustness/coverage (no product
  bugs).** Docs read consistently; no stale BF16/GPU-unverified contradiction survives.

## Findings + disposition (dedup)

| # | Sev | Axis | Finding | Disposition |
|---|-----|------|---------|-------------|
| 1 | High | Tests | `test_no_bf16_base_mount` source check `split(":",1)[0].endswith("Cosmos3-Nano")` is defeated by the `${VAR:-default}` form (truncates at the first `:`), a false-negative that could mask a re-added BF16 base. | **FIXED** — replaced with `re.search(r"Cosmos3-Nano(?![-\w])", v)` over the raw string (catches the bare base in literal or `${VAR:-default}` form; excludes `-FP8-`/`-NVFP4-` dirs). Kept the `/models/base` target check. |
| 2 | High | Tests | Overlay-include check inspected only `fp8.yml`'s direct `include:` (not transitive/other stacks). | **FIXED** — now checks base+fp8+nvfp4 include lists. (Largely moot: the file-deletion test + the render gate already preclude it, but hardened.) |
| 3 | High | Tests | No test for the "nvfp4 stays renderable" spec requirement. | **FIXED** — added `test_nvfp4_stack_renders_structurally` (structural parse; the full `docker compose config` exit-0 render remains a deterministic gate). |
| 4 | High | Tests | `--gpu-memory-utilization` parse assumed `--flag value` list form; `--flag=value` or reorder would raise instead of asserting. | **FIXED** — parser now handles both forms and raises a clear `AssertionError` if the flag is absent. |
| 6 | Med | Tests | No assertion that the api image is lean/torch-free (spec scenario). | **FIXED** — added `test_api_dockerfile_is_lean_torch_free` (no CUDA base, no vLLM/oracle install, lean `uv sync`). Full build-test stays in the GPU/integration gate. |
| 5 | Med | Tests | The ~26 GiB footprint figure itself is not unit-tested. | **No change** — GPU-measured; the AM-S4 all-modes smoke records actual peak VRAM. Not unit-testable. |
| S1 | Low | Readability | `make down` cleans both stacks — non-obvious. | **FIXED** — added a one-line Makefile comment. |
| S2 | Nit | Readability | `.env.example` `COSMOS3_MODEL_DIR` comment terser than before. | **No change** — the comment is accurate and clear; the detail lives in `docs/model_setup.md`. |

## Outcome

No Critical/High **product** findings (correctness + security PASS). All four High
test-robustness findings fixed and re-verified (`tests/deploy` = 11 passed, exit 0);
the tests are the deterministic guardrails for INV-4, so hardening them was in-scope.
Two items consciously not changed (untestable GPU figure; a clear nit). Proceed to the
GPU all-modes smoke, then the fresh-context adversarial verifier against the full
evidence.
