# Evidence Map - GPU Release Readiness and Upstream Quant Contribution

Date: 2026-07-08

Rules:

- Claims without evidence are marked speculative.
- Speculative claims cannot become MUST-level requirements.
- Owner decisions can become contract constraints, but technical feasibility
  still needs verification by the owning session.
- This repository is public (post Phase-1 GO). Entries must not cite private
  hosts, private absolute paths, or private-only artifacts; use the archived
  Phase-1 docs (`docs/archive/phase-1/**`) as historical source, not as a
  channel for reintroducing private evidence.

| Claim | Evidence | Source | Confidence | Gap / Risk |
|---|---|---|---|---|
| `docs/archive/phase-1/` now holds the full Phase-1 contract pack, handoffs, session artifacts, and `mig_s*` eval-corpus entries. | `git status` recorded 165 renamed paths after the archive move; top-level `docs/` retains only `model_setup.md`, `release_checklist.md`, `agent_workflow/**`, and the fresh Phase-2 pack. | Local repository check, 2026-07-08 | High | None; mechanical move, verified by git status. |
| The public `deploy/vllm-omni.Dockerfile` fails at build step 3/3: `pip install --break-system-packages` is unsupported by the base image's pip 22.0 (Ubuntu 22.04). | Build attempt recorded during the post-GO GPU gate. | `docs/archive/phase-1/risk_register.md` R-13; `docs/release_checklist.md` §6 | High | The rework is unproven until `GPU-S1` runs the new recipe. |
| The `-runtime` CUDA base lacks a build toolchain, and the Dockerfile's `CMD` invokes the wrong entrypoint. | Same build attempt. | `docs/archive/phase-1/risk_register.md` R-13; `docs/release_checklist.md` §6 | High | The exact replacement base tag is not yet chosen or verified for sm_120. |
| The fork's own Docker pattern is `FROM vllm/vllm-openai:v0.24.0` plus `uv pip install .`, not a from-scratch CUDA-devel build. | Fork's `docker/Dockerfile.cuda`. | `docs/archive/phase-1/next_phase_handoff.md` | High | Whether that base tag (or whichever tag `GPU-S1` chooses) supports sm_120/Blackwell is unverified until `GPU-S1` runs it. Speculative until then. |
| The confirmed vLLM-Omni serve entrypoint is `vllm serve <checkpoint-dir> --omni --host 0.0.0.0 --port 8000 …`. | Fork's `recipes/cosmos3/Cosmos3-Nano.md`, confirmed during the post-GO GPU gate. | `docs/release_checklist.md` §6 | High | None; already exercised once against a prebuilt image. |
| Both HF checkpoints ship a stale top-level `model.safetensors.index.json` referencing 7 non-existent shards; the real weight is a single consolidated file (drift D1). | GPU gate run, 2026-07-08. | `docs/archive/phase-1/risk_register.md` R-03; `docs/archive/phase-1/session_4/drift_report.md` | High | The root-cause fix (removing the index at the HF-repo level) is unproven until `GPU-S2` runs it. |
| Small config/tokenizer files on both HF repos are LFS-tracked, so a plain `git clone` leaves them as unresolved pointers; `hf download` avoids this. | GPU gate notes, 2026-07-08. | `docs/release_checklist.md` "GPU gate exercised" section | High | The LFS-tracking fix itself is unproven until `GPU-S2` runs it. |
| The pinned vLLM-Omni fork commit is `697035018b70cef76b974a909d23371a9984c3f2`. | `git ls-remote` against the public fork branch/tag. | `docs/archive/phase-1/evidence_map.md` | High | Stable as long as `GPU-S1` continues to pin by this commit; `GPU-S4` may add commits on top for the upstream contribution but must not change this pin. |
| T2I generation was proven end to end for FP8 and NVFP4 on an RTX 5090, but using a prebuilt local image (`vllm-omni-local:c89089a4`), not a build from the pinned commit via the public Dockerfile. | Post-GO GPU gate, 2026-07-08. | `docs/release_checklist.md` "GPU gate exercised" section | High | This is exactly the gap `GPU-S1` and `GPU-S3` close. |
| HF write access to `wfen/*` and the RTX 5090 host are available prerequisites for this work. | Owner decision recorded while scoping this phase. | `docs/archive/phase-1/next_phase_handoff.md` | High | Owner-stated; not independently re-verified in this blueprint pass. |
| Upstream `vllm-project/vllm-omni` `main` does not yet implement FP8/NVFP4 blockwise quant or ModelOpt-native detection. | None yet — not checked from this repository. | Assumption carried from the Task C framing in `docs/archive/phase-1/next_phase_handoff.md` | Speculative | `GPU-S4`'s first job is to verify this before any contribution code is written. Cannot become a MUST-level premise until then. |
| The fork's `precheck-pr` skill and `CONTRIBUTING.md` guidance are available and current in the `fengwang/vllm-omni` fork checkout. | Referenced by path in the handoff; no `.claude/skills/precheck-pr` exists in this repository (confirmed absent here). | `docs/archive/phase-1/next_phase_handoff.md` | Speculative | Assumed present in a different repository, not verified from here. `GPU-S4`/`GPU-S5` must confirm it exists and is current before relying on it. |
| A local checkout of the `fengwang/vllm-omni` fork was present as a sibling directory in this development environment, at HEAD equal to the pinned commit `697035018b70cef76b974a909d23371a9984c3f2`. | Confirmed during the adversarial review pass, 2026-07-08. | Local repository check, 2026-07-08 | High | Environment-specific; a later session must not assume this checkout exists elsewhere, and must still verify state against the public GitHub remote rather than relying solely on a local copy. |
