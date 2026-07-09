# Session 2 Implementation Plan - vLLM-Omni Patch Rebase And Public Pin

Date: 2026-07-06
Session: MIG-S2

## Task 1 - Planning And Baseline

Micro-steps:

1. Write the Session 2 planning artifacts under `docs/session_2/**`.
2. Record baseline failure classifications in `docs/session_2/failure_arbiter.md`.
3. Run:

```bash
rtk git status --short --branch
rtk git remote -v
rtk git log --oneline -n 20
```

4. In `vllm-omni`, run:

```bash
rtk git status --short --branch
rtk git remote -v
rtk git log --oneline -n 20
rtk python -m compileall vllm_omni
```

5. Commit point: planning artifacts complete and reviewed locally; no source
   commit required unless the owner requests WebUI repo commits.

## Task 2 - Public Fork Branch Preparation

Micro-steps:

1. In `vllm-omni`, fetch the public fork:

```bash
rtk git fetch origin
```

2. Ensure no branch/tag collision:

```bash
rtk git ls-remote git@github.com:fengwang/vllm-omni.git refs/heads/mig-s2-cosmos3-quant-pin refs/tags/cosmos3-nano-webui-mig-s2
```

3. Create the branch from public `origin/main`:

```bash
rtk git switch -C mig-s2-cosmos3-quant-pin origin/main
```

4. Record the source patch list locally. Do not commit the private checkout path,
   private branch name, or source hashes into public docs:

```bash
rtk git -C "$AUTHORIZED_SOURCE_CHECKOUT" rev-list --reverse --oneline "$AUTHORIZED_SOURCE_RANGE"
```

5. First test to write or identify:

```bash
rtk pytest -q tests/diffusion/model_loader/test_modelopt_native.py
```

Before patch replay this test is expected to be missing. Classify as expected
pre-implementation evidence rather than source failure.

6. Commit point: external fork branch exists locally at public base.

## Task 3 - Patch Replay And Conflict Resolution

Micro-steps:

1. Replay the eight authorized commits in order:

```bash
rtk git cherry-pick "$PATCH_COMMIT_1"
rtk git cherry-pick "$PATCH_COMMIT_2"
rtk git cherry-pick "$PATCH_COMMIT_3"
rtk git cherry-pick "$PATCH_COMMIT_4"
rtk git cherry-pick "$PATCH_COMMIT_5"
rtk git cherry-pick "$PATCH_COMMIT_6"
rtk git cherry-pick "$PATCH_COMMIT_7"
rtk git cherry-pick "$PATCH_COMMIT_8"
```

If Git cannot see the source commits by hash in the public checkout, add the
private/local source as a temporary local-only remote. Keep the real path and
branch in the shell environment only:

```bash
rtk git remote add local-cosmos3-source "$AUTHORIZED_SOURCE_CHECKOUT"
rtk git fetch local-cosmos3-source "$AUTHORIZED_SOURCE_BRANCH"
```

2. On conflict, stop and classify the conflict before resolving. Allowed conflict
   files are:

```text
vllm_omni/diffusion/model_loader/checkpoint_adapters/**
vllm_omni/diffusion/model_loader/diffusers_loader.py
vllm_omni/diffusion/models/cosmos3/**
vllm_omni/quantization/**
tests/diffusion/model_loader/**
tests/diffusion/models/cosmos3/**
tests/diffusion/quantization/**
tests/model_executor/quantization/**
```

3. After each topical group, run the smallest relevant check:

```bash
rtk python -m compileall vllm_omni/diffusion/model_loader/checkpoint_adapters vllm_omni/quantization
rtk pytest -q tests/diffusion/model_loader/test_modelopt_native.py
rtk pytest -q tests/diffusion/model_loader/test_modelopt_native_nvfp4.py
rtk pytest -q tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py
```

4. Self-critique after each group:

- Spec adherence: did the change satisfy only the current spec scenario?
- Edge cases: malformed sidecar, unsupported quant config, missing checkpoint files.
- Security/safety: no private paths, no unsafe downloads in tests.
- Test quality: tests assert behavior, not implementation trivia.

5. Stop after three generate-critique-fix iterations per task. If the same
   failure repeats twice, append a Failure Arbiter entry before trying another
   fix.

6. Commit point: each cherry-picked source commit remains a preserved fork commit.

## Task 4 - Deterministic Checks

Micro-steps:

1. Create/use the venv:

```bash
rtk python -m venv .venv-mig-s2
rtk .venv-mig-s2/bin/python -m pip install -U pip
rtk .venv-mig-s2/bin/python -m pip install -r requirements/common.txt
rtk .venv-mig-s2/bin/python -m pip install pytest pytest-mock
```

2. Run compile checks:

```bash
rtk .venv-mig-s2/bin/python -m compileall vllm_omni
```

3. Run targeted tests:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q \
  tests/diffusion/model_loader/test_modelopt_native.py \
  tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py \
  tests/diffusion/model_loader/test_modelopt_native_nvfp4.py \
  tests/diffusion/models/cosmos3/test_cosmos3_nvfp4_load_guard.py \
  tests/diffusion/quantization/test_fp8_blockwise_w8a16.py
```

4. Run the NVFP4 config test at the actual path. If the contract path still does
   not exist, record the classification:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/model_executor/quantization/test_nvfp4_blockwise_config.py
```

5. Full-ish targeted command after path disposition:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q \
  tests/diffusion/model_loader/test_modelopt_native.py \
  tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py \
  tests/diffusion/model_loader/test_modelopt_native_nvfp4.py \
  tests/diffusion/models/cosmos3/test_cosmos3_nvfp4_load_guard.py \
  tests/diffusion/quantization/test_fp8_blockwise_w8a16.py \
  tests/model_executor/quantization/test_nvfp4_blockwise_config.py
```

6. Commit point: deterministic checks pass or have recorded owner-acceptable
   classifications.

## Task 5 - Public Pin Publication

Micro-steps:

1. Confirm branch state:

```bash
rtk git status --short --branch
rtk git log --oneline -n 12
```

2. Push branch:

```bash
rtk git push origin mig-s2-cosmos3-quant-pin
```

3. Create and push tag:

```bash
rtk git tag -f cosmos3-nano-webui-mig-s2
rtk git push -f origin refs/tags/cosmos3-nano-webui-mig-s2
```

4. Verify remote state:

```bash
rtk git ls-remote git@github.com:fengwang/vllm-omni.git refs/heads/mig-s2-cosmos3-quant-pin refs/tags/cosmos3-nano-webui-mig-s2
```

5. Record install command:

```bash
pip install "git+https://github.com/fengwang/vllm-omni.git@cosmos3-nano-webui-mig-s2"
```

6. Commit point: public fork branch and tag verified.

## Task 6 - Review, Verification, And Handoff

Micro-steps:

1. Generate fork diff evidence:

```bash
rtk git diff --stat origin/main...HEAD
rtk git diff --name-status origin/main...HEAD
```

2. Run sharded review using the saved prompt axes:

- correctness
- security/safety
- tests
- architecture/maintainability
- performance

3. Fix only High/Critical findings with concrete evidence.
4. Re-run affected targeted checks.
5. Run adversarial verification against:

- `docs/session_2_contract.yaml`
- `docs/project_contract.md`
- fork diff
- Session 2 evidence

6. Update:

- `docs/session_2/sharded_review.md`
- `docs/session_2/adversarial_verification.md`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/handoff.md`
- `docs/eval_corpus/**` if an issue was caught or missed and the lifecycle
  requires a seed.

7. Commit point: final handoff and evidence complete; WebUI repo commit only if
   requested or required by the owner.
