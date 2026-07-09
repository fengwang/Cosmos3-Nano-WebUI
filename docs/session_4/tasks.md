# Session 4 Tasks

## 1. Upstream State Finding

- [x] 1.1 Add or verify the external fork `upstream` remote and fetch current `main`.
- [x] 1.2 Record upstream refs, fork refs, and checkout state.
- [x] 1.3 Run exact and semantic upstream searches for FP8/NVFP4 blockwise and ModelOpt-native detection.
- [x] 1.4 Write `docs/session_4/upstream_state.md` before any isolation commit.
- [x] 1.5 If upstream already covers the feature, update evidence, risk, handoff, and stop code work. Outcome: early exit not taken because upstream lacks the native blockwise sidecar adapters and quant config files.

## 2. Isolated Branch Construction

- [x] 2.1 Create the isolated branch from `upstream/main`.
- [x] 2.2 Import the FP8/NVFP4 quantization files from fork pin `697035018b70cef76b974a909d23371a9984c3f2`.
- [x] 2.3 Import checkpoint adapters and registration hooks from the fork pin.
- [x] 2.4 Import the isolated NVFP4 W4A4 `weight_scale` NaN-clamp hunk. Outcome: no import needed because upstream already contains this hunk.
- [x] 2.5 Import or adapt narrow CPU tests for touched quant-loader surfaces.
- [x] 2.6 Remove or rewrite any Cosmos3-specific imports, paths, comments, or fixtures from the upstream-facing slice.

## 3. Targeted Verification And Fixes

- [x] 3.1 Run the smallest targeted pytest set for the imported FP8/NVFP4 loader surfaces.
- [x] 3.2 Run a no-Cosmos3 dependency sweep on the branch diff and touched files.
- [x] 3.3 Run `python -m compileall vllm_omni`.
- [x] 3.4 Classify any failing check with the Failure Arbiter before fixing.
- [x] 3.5 Record conflict-resolution and semantic-drift notes.

## 4. Branch Publication And Documentation

- [x] 4.1 Push the verified branch to `fengwang/vllm-omni`.
- [x] 4.2 Record branch name, commit SHA, upstream-state finding, and checks in `docs/session_4/`.
- [x] 4.3 Update `docs/evidence_map.md`, `docs/risk_register.md`, and `docs/eval_seed_cases.md`.
- [x] 4.4 Run sharded review because session risk is medium.
- [x] 4.5 Fix only High or Critical review findings, then re-check.
- [x] 4.6 Run adversarial verification.
- [x] 4.7 Update `docs/handoff.md`.
