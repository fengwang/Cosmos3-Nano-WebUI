# Evidence Map - GitHub Migration Public Beta

Date: 2026-07-06

Rules:

- Claims without public evidence are marked speculative.
- Speculative claims cannot become MUST-level shipped behavior.
- Owner decisions can become contract constraints, but technical feasibility still
  needs verification.
- Private source repositories, private absolute paths, and private evidence are
  not cited in this public evidence map.

| Claim | Evidence | Source | Confidence | Gap / Risk |
|---|---|---|---|---|
| The public WebUI remote exists and currently has a small seed history. | `git ls-remote git@github.com:fengwang/Cosmos3-Nano-WebUI.git HEAD 'refs/heads/*'` returned `c3983f7...` for `main`. | Public GitHub remote check, 2026-07-06 | High | The local `blueprint` branch may contain extra draft state until pushed. |
| The current working repo has no `docs/` directory before this blueprint pack. | `rtk ls -la docs` failed with "No such file or directory". | Local public-repo working tree check, 2026-07-06 | High | This pack creates the initial public migration docs. |
| The WebUI seed repo has `misc/logo.png`, an empty `README.md`, and README guidance under `references/readme.howto.md`. | File tree inspection showed those files; `README.md` has 0 lines. | Local public-repo working tree check, 2026-07-06 | High | README is intentionally planned for `MIG-S7`, not this docs pass. |
| The GitHub `vllm-omni` fork exists and `main` currently points at `d4a869fe...`. | `git ls-remote git@github.com:fengwang/vllm-omni.git HEAD 'refs/heads/*'` returned `d4a869fe...`. | Public GitHub remote check, 2026-07-06 | High | Cosmos3 patch availability in the fork must be verified and pinned in `MIG-S2`. |
| `MIG-S2` published the Cosmos3 vLLM-Omni patch pin publicly. | `rtk git ls-remote git@github.com:fengwang/vllm-omni.git refs/heads/mig-s2-cosmos3-quant-pin refs/tags/cosmos3-nano-webui-mig-s2` returned `697035018b70cef76b974a909d23371a9984c3f2` for both branch and tag. | Public GitHub remote check, 2026-07-06 | High | Later sessions must depend on the tag or commit, not the mutable branch alone. |
| The pinned vLLM-Omni fork passed Session 2 deterministic checks in the isolated venv. | `rtk .venv-mig-s2/bin/python -m compileall vllm_omni` passed; expanded targeted pytest passed `118 passed, 22 warnings`. | Local deterministic checks in `/workspace/github.repo/vllm-omni`, 2026-07-06 | High | GPU inference, Docker install, and public checkpoint compatibility remain later-session gates. |
| The FP8 Hugging Face checkpoint repo exists. | The model page for `wfen/Cosmos3-Nano-FP8-Blockwise` is reachable and shows model metadata. | https://huggingface.co/wfen/Cosmos3-Nano-FP8-Blockwise, checked 2026-07-06 | High | File layout and runtime compatibility must be verified in `MIG-S4`. |
| The NVFP4 Hugging Face checkpoint repo exists. | The model page for `wfen/Cosmos3-Nano-NVFP4-Blockwise` is reachable and shows model metadata. | https://huggingface.co/wfen/Cosmos3-Nano-NVFP4-Blockwise, checked 2026-07-06 | High | File layout and runtime compatibility must be verified in `MIG-S4`. |
| Both public HF checkpoint pages currently show `openmdw-1.0` as the model license. | The model pages show "License: openmdw-1.0". | HF model pages, checked 2026-07-06 | High | README must separate repo MIT license from model license. |
| The FP8 model card is populated with a blockwise FP8 recipe and quickstart text. | The FP8 page includes recipe, quickstart, dependencies, checkpoint contents, and quality summary sections. | FP8 HF model page, checked 2026-07-06 | Medium | The WebUI runtime must verify whether the public artifact matches the expected final runtime state. |
| The NVFP4 model card appears empty. | The NVFP4 page states that `README.md` exists but content is empty. | NVFP4 HF model page, checked 2026-07-06 | High | `MIG-S4` or `MIG-S7` should compensate with WebUI setup docs, and optionally update the model card outside this repo. |
| The public beta should use external weights rather than Git or image-baked weights. | Owner selected external weights with explicit download/setup. | Owner decision in migration planning, 2026-07-06 | High | Docker and README must enforce this with scans and examples. |
| The first milestone should use CPU-only GitHub Actions plus manual GPU gates. | Owner selected CPU-only CI plus manual GPU validation. | Owner decision in migration planning, 2026-07-06 | High | GPU regressions can escape CI; `MIG-S8` must review manual evidence. |
| The first milestone should not migrate legacy plain vLLM or TensorRT-LLM submodules. | Owner selected no initial migration for those submodules. | Owner decision in migration planning, 2026-07-06 | High | If imported code still depends on them, `MIG-S3` must either remove the dependency or stop for owner decision. |
| Full API/WebUI product behavior after migration is not yet public-verified. | No migrated public source, CI run, Docker build, HF compatibility result, or GPU evidence exists yet in this repo. | Current public repo state and public evidence policy | High | All runtime claims are gates in `MIG-S3` through `MIG-S8`, not blueprint-time MUST claims. |
| `MIG-S1` recorded the public repo baseline and scope artifacts for later migration sessions. | `docs/session_1/inventory.md`, `docs/session_1/import_manifest.md`, `docs/session_1/exclusion_manifest.md`, and `docs/session_1/scrub_checklist.md` were created. | Local Session 1 docs, 2026-07-06 | High | Later sessions must re-run scans after importing source or editing public docs. |
| Current Session 1 baseline scans found no private-reference, weight/media, archive/cache, or legacy-submodule file-path matches outside scan documentation. | Fallback private-reference scan, `rg --files` extension/path scans, archive/cache scans, and legacy-submodule path scan returned no matches. | Local deterministic checks during `MIG-S1`, 2026-07-06 | High | `$PRIVATE_REF_PATTERN` was unset; the fallback pattern is a baseline, not a substitute for known private names in later sessions. |
