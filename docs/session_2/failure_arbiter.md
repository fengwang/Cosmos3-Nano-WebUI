# UX-S2 Failure Arbiter Log

Date: 2026-07-15
Classifications made before fixing, per `docs/agent_workflow/prompts/failure_arbiter.md`
(BUG / SPEC_GAP / AMBIGUITY / ENVIRONMENT / TEST_BUG).

| # | Failure / decision | Category | Resolution |
|---|---|---|---|
| A1 | `rg -n "/data/models" api/` (contract check) is not zero today — 6 pre-existing `COSMOS3_MODEL_DIR` fallbacks + a comment, none in the new loader. | **AMBIGUITY** | Chose the explicit interpretation of `EV-UX-NEGPROMPT-NO-ABS-PATH`: scope the check to `api/preprocessing/negative_prompt.py` (must be clean) + assert the 6 pre-existing matches are unchanged. Loader carries zero `/data/models` literals. |
| A2 | The **api** service had no checkpoint mount / `COSMOS3_MODEL_DIR`, so the negative-prompt loader would read nothing → default silently never engages in deployment. | **BUG** (deployment) | Added a read-only `assets/` mount + `COSMOS3_MODEL_DIR` to the api service (blast-radius-permitted compose edit "if the API needs the mount"). Verified the api reads the 15 KB file in-container. |
| A3 | vLLM-Omni container aborts at startup: guardrails ON by default but `cosmos_guardrail` not installed (NVIDIA license guard). | **ENVIRONMENT** (missing dep / manual GPU gate) | Ran guardrails-off via the documented `--no-guardrails` local-run path (matches the contract posture: guardrails-on validation is out of scope; app already sent `guardrails:False`). No product code changed. |
| A4 | 720p FP8 OOMs at denoise (transformer resident); then at the untiled-VAE decode; then SIGBUS (exit 135) on the 64 MB `/dev/shm` result transfer. | **ENVIRONMENT** (GPU/host resource) | `--enable-layerwise-offload` (denoise) + `--vae-use-tiling` (decode) + `shm_size 16gb` (result). No product code changed; config only. Owner-directed to get a green artifact. |
| A5 | NVFP4 + `--enable-layerwise-offload` → `NotImplementedError: gptq_marlin_repack ... CPU backend` at startup. | **ENVIRONMENT** (kernel constraint) | NVFP4's Marlin FP4 repack is CUDA-only; offload places weights on CPU. NVFP4 runs **without** offload (4-bit weights fit resident); the per-stack compose commands diverge accordingly. |
| A6 | Earlier hypothesis "the 15 KB negative prompt causes the OOM" — disproven. | Corrected assumption | With-vs-without-negative control at the same seed: **identical** peak VRAM (embeddings pad to `max_sequence_length`). The OOMs were purely offload/resident/tiling, not the negative prompt. Recorded honestly (E-16). |
| A7 | A `git add -A` swept `.playwright-mcp/` transient scratch into a commit (out of blast radius, not gitignored). Caught by the adversarial verifier. | **BUG** (process slip) | Removed from tracking + gitignored `.playwright-mcp/`. Lesson: stage explicit paths, never `git add -A`. |
| A8 | Adversarial verifier FAILED the first pass: smoke evidence + `evidence_map`/`handoff` not yet recorded. | Lifecycle sequencing | Not a defect — the verifier ran (lifecycle step) before the evidence-recording step. Completed the evidence/handoff updates, then re-ran the verifier. |
| A9 | The WebUI negative-prompt placeholder scenario is not unit-testable (vitest `include` excludes `components/studio/**`); is that in the `tests/**` blast radius? | **AMBIGUITY** | Interpreted `tests/**` to cover test files colocated with allowed source (so `draft.test.ts` edits are in-scope) but **not** `vitest.config` infra. Verified the placeholder behaviorally via Playwright at the live run; logged the include gap as an eval seed. |
| A10 | Sharded review ran 5 axes (contract `review_axes`) not the 6 in the updated prompt (missing readability). Owner-caught. | Process error (conflicting sources) | Ran the 6th (readability) reviewer; only Nits (F8–F10). Lesson: the prompt is the authoritative how-to; `review_axes` is a minimum. |

No failure required rewriting product code to satisfy a check (all code fixes
were spec-derived; all serving changes were config for the manual GPU gate).
