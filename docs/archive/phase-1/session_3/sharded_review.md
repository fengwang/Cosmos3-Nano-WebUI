# Session 3 Sharded Review

Date: 2026-07-06
Session: MIG-S3 (high risk -> worker_plus_reviewers)
Method: 5 independent read-only reviewers (correctness, security/safety, tests,
architecture/maintainability, performance) over the `session-3` import diff +
contract + evidence. Findings deduplicated; fix policy = High/Critical mandatory,
Medium with strong evidence or 2+ reviewers, Nits optional.

## Verdict

One HIGH (docs private-value leak) and one MEDIUM (broken public doc command) were
fixed this session, plus two supporting LOW cleanups. All correctness/performance
axes passed. Remaining Medium/Low test-coverage findings are pre-existing gaps in
the imported source, routed to MIG-S5.

## Findings And Dispositions

| # | Axis | Severity | Finding | Disposition |
|---|---|---|---|---|
| R1 | Security | **HIGH** | `docs/session_3/**` (this session's own committed docs) named private values: the private source checkout path, private intranet host, and sibling private repo name — INV-1 violation, matching the MIG-S2 eval seed. The imported source tree itself was clean. | **FIXED** — redacted all literals to policy/descriptor language + generic detectors across 8 docs; MIG-S2 regression over `docs/session_3/**` now clean. FA-6. |
| R2 | Architecture | **MEDIUM** | `schemas/README.md` told public users to run `make -f deploy/Makefile schemas` etc., but `deploy/` is deferred (no Makefile exists) — broken public workflow + dangling deferred-ref (D6/INV-1). | **FIXED** — replaced with `PYTHONPATH=api python -m app.openapi_export schemas/openapi.json` + `pytest tests/test_openapi.py`; verified idempotent + in sync. |
| R3 | Architecture | LOW | `api/engines/base.py:4` docstring referenced "S3's TRT-LLM adapter" (dropped code) — the last `trtllm`/`tensorrt` string in the imported tree. | **FIXED** — clause removed; `rg trtllm\|tensorrt api tools schemas` now clean, hardening the legacy-exclusion for the adversarial pass. |
| R4 | Architecture | LOW | `tests/test_openapi.py:40` assertion message referenced the absent `deploy/Makefile`. | **FIXED** — message now points to the direct export command. |
| R5 | Correctness | — | No hollow-pass: AST resolution of all first-party imports across api/tools/tests clean; `import app.main` torch-free; 467/470 tests execute real product code; schema in sync; excluded modules unreachable. | No action. |
| R6 | Performance | — | No repo bloat (only `misc/logo.png` 121 KB + lockfiles are binary/large); `import app.main` ~0.16 s, no import-time network/IO/subprocess; no new leaks in health/readiness. | No action. |
| R7 | Tests | MEDIUM (1 reviewer) | Torch-free `count_tokens` heuristic fallback (`reasoning.py` / `main.py:76`) is unasserted — a boundary bug could admit an over-cap prompt in CPU deploy. | **DEFERRED to MIG-S5** — pre-existing coverage gap in imported source, not introduced by S3; add a `tokenizer=None` boundary test in CI stabilization. Eval seed added. |
| R8 | Tests | LOW | `tools/checkpoint_prep/safetensors_io.py:parse_header` has only numpy-skipped coverage; near-tautology at `test_vllm_omni_client.py:76`; unpinned `pytest.raises(ImportError)` at `test_reasoner_preflight_unit.py:180`; `test_collect.py` is a venv gate. | **DEFERRED to MIG-S5** — pre-existing; recorded in handoff. |

## Notes
- The broad `Refs: docs/session_N/...` / private-repo `INV-N` inline citations in
  ~42+ imported files were reviewed and confirmed non-sensitive (no host/secret/path);
  cosmetic cleanup deferred to MIG-S7 (recorded in `scrub_report.md`).
- `misc/logo.png` and the empty `README.md` are outside the S3 blast radius (S7).
