# Session 2 Execution Contract

Date: 2026-07-06
Session: MIG-S2
Risk: high
Status: Active before implementation

## Planned File Changes

External vLLM-Omni fork checkout:

- `/workspace/github.repo/vllm-omni/vllm_omni/diffusion/model_loader/checkpoint_adapters/**`
- `/workspace/github.repo/vllm-omni/vllm_omni/diffusion/model_loader/diffusers_loader.py`
- `/workspace/github.repo/vllm-omni/vllm_omni/diffusion/models/cosmos3/**`
- `/workspace/github.repo/vllm-omni/vllm_omni/quantization/**`
- `/workspace/github.repo/vllm-omni/tests/diffusion/model_loader/**`
- `/workspace/github.repo/vllm-omni/tests/diffusion/models/cosmos3/**`
- `/workspace/github.repo/vllm-omni/tests/diffusion/quantization/**`
- `/workspace/github.repo/vllm-omni/tests/model_executor/quantization/**` only if required to preserve the selected patch's test taxonomy.

WebUI repo:

- `docs/session_2/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/handoff.md` because the user lifecycle explicitly requires Session End
  handoff updates.
- `docs/eval_corpus/**` only if a caught or missed issue requires an eval seed.

## Allowed Blast Radius

Allowed by `docs/session_2_contract.yaml`:

- external vLLM-Omni fork repository branches
- external vLLM-Omni fork tests for touched surfaces
- `docs/session_2/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`

Lifecycle-authorized additions:

- `docs/handoff.md`
- `docs/eval_corpus/**` if needed

Forbidden:

- WebUI runtime source outside docs
- model weight files
- Docker publishing workflows
- GitHub secrets or registry credentials
- legacy plain vLLM or TensorRT-LLM submodule import into the WebUI repo

## First Test To Write Or Identify

First spec-derived test:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native.py
```

Before patch replay this file is expected to be missing from public fork `main`.
That is the failing/missing test that motivates importing the first adapter
commit. The first implementation task must make this test available and then
make it pass or classify its failure.

## Checks After Each Task

Planning:

```bash
rtk git status --short --branch
rtk git diff --check
```

Fork branch prep:

```bash
rtk git status --short --branch
rtk git log --oneline -n 12
```

Adapter task:

```bash
rtk .venv-mig-s2/bin/python -m compileall vllm_omni/diffusion/model_loader/checkpoint_adapters
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native.py
```

NVFP4 task:

```bash
rtk .venv-mig-s2/bin/python -m compileall vllm_omni/diffusion/model_loader/checkpoint_adapters vllm_omni/quantization vllm_omni/diffusion/models/cosmos3
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native_nvfp4.py tests/diffusion/models/cosmos3/test_cosmos3_nvfp4_load_guard.py
```

FP8 W8A16 task:

```bash
rtk .venv-mig-s2/bin/python -m compileall vllm_omni/diffusion/model_loader/checkpoint_adapters vllm_omni/quantization vllm_omni/diffusion/models/cosmos3
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py tests/diffusion/quantization/test_fp8_blockwise_w8a16.py
```

Full Session 2 fork checks:

```bash
rtk .venv-mig-s2/bin/python -m compileall vllm_omni
rtk .venv-mig-s2/bin/python -m pytest -q \
  tests/diffusion/model_loader/test_modelopt_native.py \
  tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py \
  tests/diffusion/model_loader/test_modelopt_native_nvfp4.py \
  tests/diffusion/models/cosmos3/test_cosmos3_nvfp4_load_guard.py \
  tests/diffusion/quantization/test_fp8_blockwise_w8a16.py \
  tests/model_executor/quantization/test_nvfp4_blockwise_config.py
```

Remote pin check:

```bash
rtk git ls-remote git@github.com:fengwang/vllm-omni.git refs/heads/mig-s2-cosmos3-quant-pin refs/tags/cosmos3-nano-webui-mig-s2
```

## Failure Classification Rule

No source fix is allowed until the failing command is classified as one of:

- BUG
- SPEC_GAP
- AMBIGUITY
- ENVIRONMENT
- TEST_BUG

Repeated same failure twice triggers a new Failure Arbiter entry before another
fix attempt.

## Review Axes

Run sharded review because risk is high:

- correctness
- security/safety
- tests
- architecture/maintainability
- performance

Reviewers must report severity, evidence, violated contract clause if any,
impact, smallest safe fix, and confidence. Only High/Critical findings are
mandatory to fix in this session.

## Adversarial Verifier Brief

Fresh-context verifier sees only:

- `docs/project_contract.md`
- `docs/session_2_contract.yaml`
- `docs/session_2/**`
- fork diff from public `origin/main` to final branch
- check outputs and remote `ls-remote` evidence

The verifier tries to disprove:

- the public fork contains the selected patch line
- the tag/commit exists publicly
- deterministic checks passed or were correctly classified
- WebUI install target is a public tag or commit, not a local branch
- changed files stay inside the allowed blast radius
- evidence/risk/handoff records are sufficient for `MIG-S3`, `MIG-S4`, and `MIG-S6`

## Done Condition

`GATE-MIG-S2-VLLM` passes only when all are true:

- the selected patch line is present in the public vLLM-Omni fork branch
  `mig-s2-cosmos3-quant-pin`;
- tag `cosmos3-nano-webui-mig-s2` resolves publicly to the final accepted commit;
- deterministic compile and targeted tests pass, or failures are classified and
  dispositioned;
- the WebUI repo records the public pin, install command, test summary, conflict
  notes, limitations, evidence, and risk updates;
- sharded review and adversarial verification have PASS or accepted
  classifications for any failure.

