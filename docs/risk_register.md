# Risk Register - GPU Release Readiness and Upstream Quant Contribution

Date: 2026-07-08

Status values are blueprint-time. Sessions update rows with evidence as they
close. Where a row advances or closes a Phase-1 risk, the archived ID is
noted; see `docs/archive/phase-1/risk_register.md` for that history.

| ID | Risk | Probability | Impact | Owner Session | Mitigation / Gate | Status |
|---|---|---:|---:|---|---|---|
| R-01 | The public base image (`vllm/vllm-openai:<version>`) does not support sm_120/Blackwell, so the from-source build still cannot produce a working image. | Medium | High | GPU-S1 | Confirm the chosen base tag's CUDA/torch build supports sm_120 before committing to it; record the check. Advances archived R-13. | Open - blueprint-time. |
| R-02 | Fixing the `wfen/*` Hugging Face repos changes their revision hashes and breaks any early adopter who already cloned or downloaded the beta-GO revision. | Low | Medium | GPU-S2 | Document the revision change in the model card / release notes; this is a one-time public-beta cost, not a recurring one. | Open - blueprint-time. |
| R-03 | The re-pin sweep misses a reference (a file, a comment, an eval case) after the Hugging Face revisions change, leaving a stale pin somewhere in the repo. | Medium | Medium | GPU-S2 | Run an exact-match `rg` sweep for the old revision SHAs across the whole repo, not only the four named files, before closing the session. | Open - blueprint-time. |
| R-04 | Migrating small files out of LFS accidentally also de-tracks a large weight file from LFS, bloating repository history. | Low | High | GPU-S2 | Apply the LFS rule by explicit file-size/type check, not a blanket `.gitattributes` rewrite; diff the LFS-tracked file list before and after. | Open - blueprint-time. |
| R-05 | The `GPU-S1` image builds and the `GPU-S2` checkpoints load individually, but T2I/T2V still fails together for a reason other than the already-known drift D1. | Medium | High | GPU-S3 | Run the joint validation as its own session with full evidence fields, not as an assumed consequence of GPU-S1 and GPU-S2 each passing alone. Advances archived R-03 and R-13. | Open - blueprint-time. |
| R-06 | Upstream `vllm-project/vllm-omni` `main` has drifted enough that the isolated quant commits do not rebase cleanly, or upstream already has overlapping/conflicting quant code. | Medium | Medium | GPU-S4 | Check upstream state before isolating any code; resolve conflicts only in the isolated quant-loader surface, escalating anything Cosmos3-specific to the owner. | Open - blueprint-time. |
| R-07 | The quant contribution cannot be fully decoupled from Cosmos3-specific code without breaking a guard or adapter the fork depends on. | Medium | Medium | GPU-S4, GPU-S5 | Isolate model-agnostic files first (`GPU-S4`); if a dependency cannot be cut cleanly, stop and record the coupling rather than shipping a partially-decoupled PR. | Open - blueprint-time. |
| R-08 | DCO sign-off, upstream CLA, or maintainer review stalls or blocks the pull request indefinitely. | Medium | Low | GPU-S5 | Confirm DCO/CLA requirements and run `precheck-pr` before submission; a stalled PR is a known, accepted outcome, not a release blocker for this repository. | Open - blueprint-time. |
| R-09 | The RTX 5090 host is unavailable or contended during `GPU-S1`/`GPU-S3`, blocking build or validation work. | Low | Medium | GPU-S1, GPU-S3 | Treat GPU host availability as a session precondition; record the conflict and reschedule rather than substituting an unverified environment. | Open - blueprint-time. |
