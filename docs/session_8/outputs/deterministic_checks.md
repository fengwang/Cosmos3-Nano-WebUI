# Deterministic Checks - MIG-S8 Release Gate

Date: 2026-07-07 · Branch: `session-8` · Host: RTX 5090 present (no GPU inference this session)

All CPU checks re-run this session. `rtk` filters stdout for token savings; **exit codes and
the JUnit XML are authoritative**. The pytest count is taken from JUnit
(`<testsuite tests=… failures=… errors=… skipped=…>`), not the filtered console tail.

## Checks run (evidence of record)

| # | Check | Command | Result | Verdict |
|---|---|---|---|---|
| 1 | Repo state | `git status --short --branch` | `## session-8`, working tree clean | PASS |
| 2 | Python env | `uv sync --frozen --group test-cpu` | exit 0 — "Checked 47 packages" (torch-free) | PASS |
| 3 | Python lint | `uv run ruff check api tests` | exit 0 — "All checks passed!" | PASS |
| 4 | Python unit | `uv run pytest -m "not gpu"` | **JUnit: tests=486, failures=0, errors=0, skipped=0**, exit 0 (= S7's 485 + the 1 test added by amendment S8-A2's scanner patch) | PASS |
| 5 | WebUI deps | `pnpm install --frozen-lockfile` | exit 0 — "Already up to date" | PASS |
| 6 | WebUI build | `pnpm build` | exit 0 — Next.js build, static+dynamic routes | PASS |
| 7 | WebUI lint | `pnpm lint` (`eslint .`) | exit 0 | PASS |
| 8 | WebUI types | `pnpm typecheck` (`tsc --noEmit`) | exit 0 | PASS |
| 9 | WebUI unit | `pnpm test` (`vitest run`) | **39 files, 209 passed**, exit 0 | PASS |
| 10 | Compose FP8 | `docker compose -f deploy/docker-compose.fp8.yml config` | exit 0, **0-byte stderr**, 76 lines | PASS |
| 11 | Compose NVFP4 | `docker compose -f deploy/docker-compose.nvfp4.yml config` | exit 0, **0-byte stderr**, 76 lines | PASS |
| 12 | Private-ref scan | `uv run python tests/test_private_ref_scan.py` | **clean (0 findings)**; `SCAN_ROOTS = api, webui, tests, schemas, docs, .github` (covers `docs/session_8/**`) | PASS |
| 13 | Weight/media (tracked) | `git ls-files \| rg -i '\.(safetensors\|pt\|pth\|ckpt\|mp4\|mov\|avi\|webm)$'` | empty (no tracked weight/media) | PASS |
| 14 | Weight/media (tree) | `rg --files \| rg -i '\.(safetensors\|pt\|pth\|ckpt\|mp4\|mov\|avi)$'` | empty | PASS |
| 15a | S8 lockfile URL credential scan | `rg -n "://[^/[:space:]]+:[^/[:space:]]+@" uv.lock webui/pnpm-lock.yaml` | **exit 1** (no `user:pass@` in any lockfile URL) | PASS |
| 15b | S8 absolute local-path scan (corrected) | `git ls-files \| while read f; do rg -noH "/(home\|Users\|root\|workspace\|mnt\|data/home)/[A-Za-z0-9._/-]+" "$f"; done`, post-filtering `/path/to/`, `/home/runner` (public GH runner), and the repo self-path | **In-radius surface CLEAN** after fixing `evidence_map.md:21` (a `/workspace/…` local path → public phrasing). **24 out-of-radius** hits in `docs/session_{2,3,4}/**` scrubbed under amendment S8-A1 (FA-2) | PASS (in-radius) / FA-2 (out-of-radius) |
| 15c | S8 private host/codename scan | `rg -niH "\b(internal\|corp\|intranet)\.[a-z]\|\.local\b\|hexagon\.com"` over tracked tree | **exit 1** besides the **intended public** `feng.wang1@hexagon.com` in `SECURITY.md`/`CODE_OF_CONDUCT.md` (R-01) | PASS |

## Checks not run (recorded with reason)

| Check | Reason | Disposition |
|---|---|---|
| `rg -n "$PRIVATE_REF_PATTERN" .` (contract literal) | `$PRIVATE_REF_PATTERN` is **unset** in this environment → empty pattern, not a meaningful scan (ENVIRONMENT) | Authoritative substitute run and clean: committed `tests/test_private_ref_scan.py` (#12) + the S8 broad-scan human gate (#15). S1/S5 precedent. |
| GitHub-hosted Actions run of `.github/workflows/ci.yml` | Nothing is pushed (`origin/main` = seed `c3983f7`); the runner cannot be exercised locally | **At-publish confirmation** (`release_checklist.md` §5). Local equivalents of every CI step are run and green above (#2–#9). |
| `EV-MIG-GPU-*` (all GPU inference: t2v/t2v_audio/i2v/t2i, forward_dynamics, reasoning, jobs-SSE, artifacts) | Owner decision 1 (defer GPU); no checkpoints mounted, no pinned-fork image built, drift D1 open | **Beta-limited manual gate** — see `gpu-beta-limited-disposition` spec + `gate_record.md`. `INV-8` satisfied (README marks each mode GPU-unverified). |
| vLLM-Omni image build (`deploy/vllm-omni.Dockerfile` from pinned `697035018b70…`) | Heavy/CUDA; owner decision 1 (defer) | Deferred manual gate (R-13); command recorded in handoff + `release_checklist.md` §6. |

## Notes

- No runtime source, schema, or dependency pin was edited; the checks are read-only /
  render-only. `uv.lock` and `pnpm-lock.yaml` are unchanged (frozen installs; `INV-10`).
- All 14 numbered CPU checks (#1–#14) passed. During sharded review, the original #15
  "absolute non-placeholder path scan" was found **silently broken** — it used an `rg`
  negative look-around `(?!Cosmos3-Nano-WebUI)`, unsupported by `rg`'s Rust regex engine, so
  `rg` exited 2 and `2>/dev/null` swallowed the error → false "clean" (classified **TEST_BUG**,
  `failure_arbiter.md` FA-1). Corrected above (#15a/#15b/#15c with exact commands + exit codes).
  The corrected scan surfaced a real `/workspace/…` local path in `evidence_map.md:21`
  (**fixed in-radius**) and 24 out-of-radius hits, all **scrubbed under owner-approved amendment
  S8-A1** (`failure_arbiter.md` FA-2). No other deterministic check failed.
- The committed scanner `tests/test_private_ref_scan.py` (#12) previously had no `/workspace/`
  pattern class or `.webm`; **owner-approved amendment S8-A2** (FA-3) added both with
  RED-before-GREEN unit tests, so the gate now catches this class. #12 re-run **clean**.
- Counts match the `MIG-S7` baseline modulo the S8-A2 addition: pytest **486** (S7 baseline
  485 + the one `test_workspace_ellipsis_form_not_flagged` test added by S8-A2), vitest **209**
  (unchanged) — no regression from the S7 close-out to the S8 release gate.
