# AM-S5 Sharded Review

Date: 2026-07-26 · Risk: high · Axes: correctness, tests, security/safety, architecture, readability, performance.
Three read-only reviewers (fresh subagents) over the full diff + evidence. Deduplicated below.

## Verdict: PASS — no Critical / High / Medium findings.

All reviewers independently confirmed: the NVFP4 wiring is a faithful, field-for-field analog of the
GPU-verified FP8 stack; the shipped patch files are byte-identical to the P2 GPU-proven prototype; the
frozen FP8 stack + `schemas/openapi.json` are byte-unchanged; blast radius is clean (no forbidden-file
edit, `api/` untouched); INV-1/INV-4/INV-5/INV-8 hold; the new tests were **mutation-confirmed to have
teeth** (dropping the reasoner, adding offload, sneaking a BF16 mount, flipping the quant, or dropping the
reasoner from the stop line each fail a specific assertion).

Deterministic gates re-run by reviewers: `uv run pytest -m "not gpu"` green; `tests/deploy` green;
`git diff --exit-code deploy/docker-compose.fp8.yml schemas/openapi.json` clean; `test_private_ref_scan`
clean; both stacks `docker compose config` render.

## Findings (Low / Nit) + disposition

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | Low | `docker-compose.nvfp4.yml` omni comment ("resident ~16.3 GiB / Peak ~18.5 GiB", pre-existing UX-S2 720p figures) reads as drift vs AM-S5's measured t2i ~17.1 / action ~18.2 GiB. | **FIXED (clarified):** added an AM-S5 note with the P1-measured t2i/action peaks; the 16.3 GiB (weights-resident) / 18.5 GiB (720p peak) figures are retained (different workload, not wrong). |
| 2 | Nit | `risk_register.md` R-05 (t2i regression) status still said "Open for AM-S4/S5" — the NVFP4 t2i non-regress (P1) was not recorded. | **FIXED:** R-05 updated with the AM-S5 NVFP4 non-regress result. |
| 3 | Nit | `get_min_capability()` returns 80 (vs FP8's 89); comment asserts sm_80+ support only verified on sm_120. | **No change** — non-load-bearing (sm_120=120 clears any ≤120 threshold; only reachable via explicit `--quantization`); correct for Marlin FP4 weight-only. |
| 4 | Nit | Dockerfile header "3-file patch (NVFP4 W4A16 text path)" — 1 of 3 files is stock `__init__`+append. | **No change** — consistent with the FP8 Dockerfile house style. |
| 5 | Nit | `from_config(cls, config)` ignores `config`. | **No change** — intentional (state built lazily to dodge the circular import); mirrors the FP8 patch exactly. |
| 6 | Nit (forward) | Both reasoners vendor the whole stock `quantization/__init__.py` → re-vendor cost on a vLLM bump. | **No change (out of scope)** — pre-existing (FP8 too); captured as the NFR-5 `fengwang/vllm` public-pin follow-up. |

Per the session workflow ("fix High/Critical only"), no finding blocked; #1/#2 applied as cheap
honesty/completeness wins. Post-fix `tests/deploy` re-run green; FP8 compose still byte-unchanged.
