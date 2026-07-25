# AM-S2 Sharded Review

Date: 2026-07-25 · Risk: high · Reviewers: two fresh-context subagents (read-only), axes:
correctness, tests, architecture, security, performance, readability. Scope: the AM-S2 diff
(repo `api/` + `deploy/` + `tests/`, the vendored fork patch `deploy/vllm-reasoner/patch/`).
Findings deduplicated; Failure-Arbiter classification applied before any fix (per the contract).

## Findings

| # | Sev (raw) | Area | Finding | Disposition |
|---|---|---|---|---|
| 1 | High | readability | `api/app/main.py` factory docstring said "REASONING branch is unchanged (R-11)" and a comment said "reasoning subprocess" — both stale (reasoning is now a container). | **FIXED** — docstring + comment updated to describe the reasoner container (honesty/accuracy). |
| 2 | "Critical" | correctness | `load_edge_tokenizer()` loads from `ReasonerConfig.model_dir`; the api mounts only the checkpoint `assets/`, so `AutoTokenizer` fails → the CPU context-cap uses the char heuristic. | **NOT A BUG / by-design (BUG→no).** The char heuristic is the *documented* D-8 fallback (conservative over-estimate; never under-caps) and the reasoner container's `--max-model-len 8192` is the hard backstop. Not a regression: on the default `make up-fp8` (no overlay) the BF16 base was never mounted, so the edge tokenizer was already on the heuristic; reasoning simply wasn't runnable there pre-AM-S2. Not INV-6 (honesty ≠ cap accuracy). → documented as an **AM-S4** mount refinement (mount the checkpoint's tokenizer subset for a tighter count). |
| 3 | High | architecture | Old subprocess reasoning path (`reasoning_spec`, `server_launch_argv`, `ReasonerConfig`, `reasoner_preflight`) is now dead in production. | **ACCEPTABLE-DORMANT per R-11** ("leaving the dormant path in place … not a required deletion"). Documented in `handoff.md` for AM-S4 cleanup (with the legacy overlay + `WITH_REASONING`). No conflict; tests kept green as regression guards. |
| 4 | Medium | consistency | `vllm-reasoner` compose service has no `COSMOS3_MODEL_DIR` env (the command hardcodes `/models/checkpoint`). | **Nit, non-functional** (path is explicit in the command). Left as-is for transitional AM-S2; AM-S4 deploy reconciliation may normalize. |
| 5 | Low | observability | `VllmReasonerStream` surfaces "container failed to start" and "unreachable at runtime" as one SSE error event. | Accepted (working as designed; the SSE error carries the exception text). |

## Confirmed correct (both reviewers, independently)
- Quant target regex `language_model\.model\.layers\.\d+\.mlp\.(gate_up_proj|down_proj)$` matches only
  the LM MLP (fused + standalone), never attention / `lm_head` / the BF16 visual tower.
- `cosmos3.py` mapper `weight_quantizer._scale`→`weight_scale` + drop `._amax` is correct for the W8A16 method.
- Factory builds the correct reasoner `ContainerPlaneWorker`; `container_reasoning_spec` is a valid HTTP-probe spec; `VllmReasonerStream` targets the container URL; tests pin the app-wired path (not a stub).
- Residency safety net (INV-5) preserved: `manager.py`/`residency.py` unchanged; both planes are containers; reasoner (~26 GiB) and omni (~13.5 GiB) cannot co-reside → evict-before-load enforced.
- Security: docker control confined (fixed name/verbs, operator env only); no SSRF (URL from env, never request); reasoner Dockerfile pins the vllm-omni commit immutably; no secret/private-path committed (INV-1).

## Verdict
No **surviving** Critical/High requiring a code change beyond finding #1 (fixed). Findings #2/#3 are
Failure-Arbiter-classified as by-design / R-11-acceptable and documented for AM-S4. Core correctness,
security, performance, and residency safety confirmed.
