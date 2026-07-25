# AM-S2 Adversarial Verification

Date: 2026-07-25 · Fresh-context verifier (subagent; did not see the implementation conversation —
only the session contract, the diff, and the evidence). Job: **falsify** GATE-AM-S2-REASONING.

## Verdict: **PASS** (could not falsify the done condition)

The verifier independently ran the deterministic gates and refuted every adversarial case.

### Independently re-run gates
- `uv run pytest -m "not gpu"` → **527 passed, 0 failed** (includes the 4 new container-wiring tests).
- `docker compose -f deploy/docker-compose.fp8.yml config` → **no BF16 mount**; `vllm-reasoner`
  mounts only the FP8 checkpoint (read-only); command `--quantization fp8_blockwise_w8a16`, no `--omni`.
- `git diff --exit-code schemas/openapi.json` → **0** (INV-8 holds).
- Confirmed the vendored patch files are byte-present in the reasoner image build context.

### Adversarial cases — all refuted
1. **Verified without an owner quality verdict?** No — `OWNER-AM-REASON-QUALITY = PASS` is recorded
   (P2), paired with the recorded end-to-end run → INV-6 satisfied.
2. **BF16 mount / overlay / `WITH_REASONING` still on the reasoning path?** No — reasoner base is
   `vllm/vllm-openai:v0.24.0` (not a BF16 CUDA base), single FP8 mount, `--quantization
   fp8_blockwise_w8a16` (no `--omni`), no overlay in `make up-fp8`, api build torch-free (INV-4).
3. **t2i silently regressed / smoke not really run?** No — P3 is a genuine run (valid PNG, magic
   `89504e47`, 691,968 bytes); the generation path is byte-unchanged by diff (INV-2).
4. **Plane-merge without an OOM-free VRAM trace?** No plane-merge adopted; swap/evict-before-load
   retained; reasoner and generation never co-reside (INV-5).
5. **Test asserts a stub reasoner, not the app-wired path?** No — tests build a real
   `ContainerPlaneWorker`, assert the container name / HTTP `/v1/models` probe / empty argv / the
   `VllmReasonerStream` container URL.

### Invariants verified: INV-1, INV-2, INV-3, INV-4, INV-5, INV-6, INV-8. Blast radius within
`allowed_files`; no forbidden files touched.

## Classification of the two non-blocking review findings (see `sharded_review.md`)
The verifier's PASS stands alongside the correctness reviewer's "edge tokenizer" and "dead code"
findings, which were Failure-Arbiter-classified as **by-design fallback** (not a regression) and
**R-11 acceptable-dormant** respectively — neither breaches the done condition.

**Conclusion:** GATE-AM-S2-REASONING is satisfied.
