# Eval Harvest — UX-S2 (Generation Defaults: Negative-Prompt Preset + 720p Video)

Date: 2026-07-15
Session outcome: GATE-UX-S2-DEFAULTS deterministic criteria PASS (CPU 518, WebUI 208,
OpenAPI in sync, no-abs-path clean); live 5090 smoke PASS for FP8 + NVFP4 720p with the
negative default applied; adversarial verifier PASS after evidence recorded.

Reusable workflow lessons, each with a proposed promotion target.

## 1. A "preset a default" session's blast radius must include the config that makes the default *serve*
- **What (SPEC_GAP, caught by the live smoke):** the contract framed UX-S2 as code-only
  defaults and permitted compose edits "**only if** the API container needs the model-assets
  mount." But the new 720p default did not serve out-of-box: (a) the **api** service had no
  checkpoint mount, so the negative-prompt loader read nothing and the default silently never
  engaged in deployment; (b) 720p FP8 OOMs without `--enable-layerwise-offload`; (c) the
  untiled-VAE decode OOMs without `--vae-use-tiling`; (d) the 720p video result SIGBUSes on the
  64 MB default `/dev/shm`. None of this is visible from CPU tests.
- **How caught:** the recommended (non-blocking) GPU smoke — which the owner elected to run live.
- **Promotion target — update project-contract template / AGENTS.md:** when a session changes a
  **default** that only manifests at serve time (resolution, precision, a file-sourced preset),
  the blast radius and the done condition MUST include the deployment path that makes the default
  actually run, and the recommended smoke should be treated as the real acceptance signal, not an
  afterthought. "The default is set in code" ≠ "the default works."

## 2. GPU-fit evidence must record the full serving config, not just peak VRAM
- **What:** the blueprint (E-08/E-09) inferred the 49-frame 720p default "should sit well under"
  the bundled 189-frame example's 31,957 MiB peak. That inference was wrong on three counts the
  evidence row never captured: the example used **layer-wise offload**, had **no negative prompt**,
  and its peak was the *denoise*, not the *untiled-VAE decode*. The naive config OOMs.
- **How caught:** the live smoke, peeling one bottleneck at a time (guardrails boot → denoise OOM →
  decode OOM → shm SIGBUS → PASS).
- **Promotion target — add eval seed / update NFR-4:** every GPU smoke row SHALL record the serving
  flags in effect (offload / tiling / shm / guardrails) alongside peak VRAM. A VRAM number without
  its config is not reproducible and invites false "fits" conclusions.

## 3. Per-precision serving quirks: NVFP4 ≠ FP8 (offload incompatibility)
- **What:** `--enable-layerwise-offload` fixes FP8 720p but **breaks NVFP4 at startup**: NVFP4's
  Marlin FP4 kernel runs `gptq_marlin_repack` (CUDA-only) in `process_weights_after_loading`, and
  offload places weights on CPU → `NotImplementedError`. NVFP4's 4-bit weights are resident-small
  enough to fit without offload. The two stacks legitimately need different commands.
- **Promotion target — add eval seed:** do not assume a memory remedy that works for one quantized
  path transfers to the other; validate FP8 **and** NVFP4 independently (the contract's FR-6 already
  required both — this is why).

## 4. Human catch — the CPU-offload insight (agents missed the fix)
- **What:** faced with the 720p FP8 OOM, the agent tried `expandable_segments` first; the **owner**
  recalled that prior phases used CPU-offload tricks, which pointed directly at
  `--enable-layerwise-offload` (documented in the archive as the 720p remedy, and visible in the
  bundled example's log). This unblocked the smoke.
- **Category:** the agent under-used the archived deep-study docs before trial-and-error.
- **Promotion target — update AGENTS.md:** before iterating on a GPU/resource failure, grep the
  archived phase docs (`docs/archive/**`) and any bundled example logs for the same symptom — the
  remedy is often already recorded there.

## 5. Human catch — followed a remembered 5-axis review instead of the updated 6-axis prompt
- **What:** `docs/agent_workflow/prompts/sharded_review.md` was updated to **6** axes (adding
  Readability/Simplicity), but the agent dispatched only the **5** listed in the session contract's
  `review_axes:` and folded readability away. The agent had read the updated prompt yet deferred to
  the shorter, familiar list. The **owner** caught the omission; the 6th reviewer was then run.
- **Category:** stale-habit / conflicting-source resolution error (chose the shorter list silently).
- **Promotion target — update CLAUDE.md / project-contract template:** the sharded-review **prompt**
  is the authoritative how-to; a session contract's `review_axes` is a minimum, not a cap. When the
  two disagree, run the superset and surface the discrepancy rather than silently picking one. Better:
  keep `review_axes` in the contract in sync with the prompt, or have the contract reference the prompt.

## 6. Adversarial verifier caught out-of-radius scratch + premature "done"
- **What:** a `git add -A` during the live-run Playwright check swept `.playwright-mcp/` transient
  files into a commit (out of blast radius, not gitignored). The verifier also correctly FAILED the
  first pass because the smoke evidence + handoff/evidence-map updates were not yet written.
- **Category:** process slip (over-broad `git add`) + lifecycle sequencing (verifier ran before the
  evidence-recording step).
- **Promotion target — update AGENTS.md + add CI check:** never `git add -A`; stage explicit paths.
  Gitignore tool scratch dirs (`.playwright-mcp/`). And record the smoke evidence into
  `evidence_map.md` **before** running the adversarial verifier, since the done condition depends on it.

## 7. Process signals that worked (keep)
- The pure/impure split (loader Action isolated; `default_dimensions` pure in `engines.base`) kept the
  change testable and let the sharded review verify INV-P5-1 cleanly.
- Running the smoke **live** (owner's call) converted a latent, wrong "fits" assumption into measured
  fact and surfaced four real deployment gaps that no CPU check could.
- Same-seed with/without-negative diff is a clean behavioral proof that a default "reaches the engine"
  when the backend does not log the value.
