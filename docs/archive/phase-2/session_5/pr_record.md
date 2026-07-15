# Session 5 PR Record

## PR Metadata

- Repository: `vllm-project/vllm-omni`
- Base branch: `main`
- Head branch: `fengwang:gpu-s4-quant-loader-isolation`
- Head SHA: `a33df880b83da06087ca4ca13eb061a567cbfe36`
- Title: `[Core][Quantization] Add ModelOpt-native FP8/NVFP4 blockwise loaders`
- Body file: `docs/session_5/pr_body.md`
- PR URL: `https://github.com/vllm-project/vllm-omni/pull/5000`
- Created at: `2026-07-09T19:41:13Z`

## DCO

Branch base: `ca0ae7269ca3e9487645cf66088fdfc338951da9`

All branch commits include `Signed-off-by: Feng <wang_feng@live.com>`:

- `22c8f916bbf333c08c196cb0f827569aaff5c365`
- `35efd2c816cfa2d9b67db5cdaa34513259416e01`
- `a33df880b83da06087ca4ca13eb061a567cbfe36`

## Owner Gate

- Status: approved.
- Approval timestamp: `2026-07-09T19:40:49Z`.
- Approval evidence: user said, "It is good to me. I approve opening the PR now."
- Important: the earlier brainstorming approval was not used as PR-opening approval; the approval above was recorded immediately before `gh pr create`.

## Submission Command

Owner gate is approved. Submission command:

```bash
gh pr create \
  --repo vllm-project/vllm-omni \
  --base main \
  --head fengwang:gpu-s4-quant-loader-isolation \
  --title "[Core][Quantization] Add ModelOpt-native FP8/NVFP4 blockwise loaders" \
  --body-file docs/session_5/pr_body.md
```

## GitHub Checks

- Final status: green as of `2026-07-09T19:48:07Z`.
- `DCO`: success.
- `pre-commit`: success.
- `Build Wheel / build (3.11)`: success.
- `Build Wheel / build (3.12)`: success.
- `docs/readthedocs.org:vllm-omni`: success.
