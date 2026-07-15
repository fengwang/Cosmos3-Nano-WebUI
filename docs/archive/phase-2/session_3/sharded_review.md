# Session 3 Sharded Review

Date: 2026-07-09. Five independent reviewers (correctness, security/safety, tests,
architecture, performance), each given `docs/session_3_contract.yaml`,
`docs/project_contract.md`, `docs/session_3/design.md`/`specs/*.md`, and
`git diff GPU-S2..GPU-S3`, per `docs/agent_workflow/prompts/sharded_review.md`.
Findings below are deduplicated across reviewers where they overlapped; outcome
recorded per finding.

## Critical

### C1 — Every generation probe mounted the stale, pre-fix checkpoint, not T1's fresh download
**Found by:** correctness. **Evidence:** `.env` pins `COSMOS3_FP8_DIR`/`COSMOS3_NVFP4_DIR`
to `/data/models/Cosmos3-Nano-*-Blockwise`, which outranks
`deploy/docker-compose.{fp8,nvfp4}.yml`'s own repo-relative default — confirmed live via
`docker compose config` and `git log` inside the mounted directory (pre-fix revision
`4e181f99…`, `BIAS.md` an unresolved LFS pointer, a `model.safetensors.index.json.stale-bak`
from a manual workaround). **Violated:** `session_3_contract.yaml` invariants (fresh
download, no manual workaround), its own adversarial case ("reuses a cached, already-fixed
local checkpoint directory"). **Outcome: FIXED.** `compose_lifecycle.bring_up()` now
overrides the env vars explicitly (verified live that process env outranks `--env-file`)
plus a preflight that fails loudly on any mount mismatch (verified it both passes for the
correct path and raises for a wrong one). T3–T7 re-run against the corrected mount; all
downstream doc claims (evidence_map.md, eval_seed_cases.md, model_setup.md,
release_checklist.md, README.md, risk_register.md) corrected to cite the re-verified
hashes/job-IDs. See commits `0fc75de`, `48f4a37`, `f3ba655`, `b0dc414`.

## High

### H1 — `run_t2v_smoke.py`'s hardware probe (and all four scripts', on inspection) had no exception boundary
**Found by:** correctness. **Outcome: FIXED.** `get_hardware_and_driver()` moved inside each
script's try boundary with an `"unknown"/"unknown"` fallback. Commit `c18a236`.

### H2 — T2V's `_attempt()` had six inline `SCOPED_OUT` returns instead of one boundary
**Found by:** architecture (same underlying issue as correctness' framing of H1/H4).
**Outcome: FIXED.** Restructured to raise internally, caught once — matches the other three
scripts' shape. `SCOPED_OUT`-for-every-failure remains the deliberate, documented choice
(design.md's error-strategy table); only the boundary shape changed. Commit `c18a236`.

### H3 — Dockerfile-freshness guard was wired into `run_direct_t2i.py` only, not `run_fullstack_t2i.py`/`run_t2v_smoke.py`
**Found by:** architecture. **Outcome: FIXED.** Moved into `compose_lifecycle.bring_up()`,
the one chokepoint all three scripts already call through. Also fixed the git-error-vs-
real-diff conflation this touched (`bool(returncode)` treated any nonzero git exit as "has a
diff"; now distinguishes exit 1 from a genuine git failure). Commit `c18a236`.

### H4 — Three mutation-confirmed test-coverage gaps in `lib.py`
**Found by:** tests (via live mutation testing against a scratch copy, never the real repo).
`evidence_record_to_dict` had zero coverage (a `.name` vs `str()` regression on `Verdict`
would silently corrupt every fragment and break `render_summary`'s PASS/FAIL compare, undetected);
`check_valid_video`'s signature check was only exercised by inputs short enough to hit the
length guard (deleting the actual signature check entirely still passed the suite);
`build_evidence_record`'s only assertion was `isinstance()`, so a
`checkpoint_repo`/`checkpoint_revision` field swap survived undetected (INV-8 risk).
**Outcome: FIXED.** Three targeted tests added (30 total, up from 25). Commit `c18a236`.

### H5 — Private absolute path committed to git history 9 times before being fixed
**Found by:** security (via `git show <sha>:<path>` across all commits between `GPU-S2` and
`GPU-S3`, not just the tip-to-tip diff). `constants.py` and every `evidence_*.json` fragment
contained the session scratchpad path (`/home/…`-shaped) and the repo's local absolute
checkout path (`/workspace/…`-shaped) across commits `fa81e11` through `ac11cb3`, before
being fixed at `be59188`.
**Violated:** `project_contract.md` INV-1 — the commit act already happened, a later fix
commit doesn't erase it from reachable history. **Outcome: NOT FIXED — owner decision
required.** The branch is not pushed anywhere (confirmed: no `GPU-S2`/`GPU-S3` remote refs),
so exposure is currently local-only, but a non-squash merge or a raw push would make these
9 commits permanently reachable. Rewriting history (`rebase`, squash) is a destructive,
hard-to-reverse operation this agent will not perform without explicit authorization — see
`docs/handoff.md` for the recommendation and options.

## Medium (deferred per "fix High/Critical only")

- Correctness: T2V's `_attempt()` can only return `SCOPED_OUT`, never `FAIL` — a genuine bug
  would be indistinguishable from an expected resource-limited scope-out. Partially
  deliberate (design.md's own error-strategy table); left as-is, flagged for a future
  session if T2V validation depth increases.
- Security: the general "subprocess exception embeds absolute paths" pathway — **actually
  fixed anyway** (see `lib.sanitize_error_text`, commit `c18a236`) despite being Medium, since
  it directly continued the H5-adjacent INV-1 work already in progress.
- Architecture: `_wait_ready` duplicated verbatim across two scripts; `REPO_ROOT` computed
  identically in six modules instead of once in `constants.py`; T2V's terminal-failure check
  narrower than the jobs API's (missing `"cancelled"`).
- Tests: `merge_evidence`'s `unexpected_task_ids` path untested; `encode_multipart`'s test
  only checks one field; `render_summary`'s hash-truncation/mode-fallback untested;
  `check_job_terminal(())` raises instead of returning the documented `FAIL`; several Action-
  script pure-calculation fragments (`container_http`'s relay parsing, request-body builders
  duplicated across three scripts, `env_probe._first_match`) are extractable and cheaply
  testable but weren't extracted.

## Low / Nit (deferred)

- Correctness: doc prose asserts "visually identical"/"independently verified via
  file/ffprobe" with no corresponding `EvidenceRecord` field.
- Architecture: `_wait_ready`'s parameter shadows the imported `compose_file` function name
  (latent trap, not a live bug); `_is_lfs_pointer` reads like a pure predicate but does I/O.
- Performance: relay/exec path has no response-size bound and fragile "last line of stdout"
  parsing (sound given the closed-loop trust model); `merge_evidence`'s `unexpected_task_ids`
  computation is O(n·m) instead of O(n+m) (irrelevant at today's fixed n=m=7).
- Performance: temp override-file leak on every `bring_up()` call — **fixed anyway** as part
  of the mount-bug fix (commit `0fc75de`'s `try/finally: os.unlink(override_path)`).

## Checked, no violation found (selected)

- Secrets/tokens never logged or written to a committed file (only used as an HTTP header
  value).
- No shell injection — every `subprocess` call uses list-form argv, no `shell=True`; the
  stdin-piped relay script is a fixed static string, request data travels as JSON.
- No generated media (image/video binaries) committed anywhere.
- Blast radius: zero touches outside `session_3_contract.yaml`'s `allowed_files`, zero
  touches inside `forbidden_files`.
- `--no-guardrails` applied only via a runtime-generated, never-committed override file,
  matching the explicit R-10 owner decision.
- ACD fidelity: every `lib.py` function is I/O/clock/network/subprocess-free; `constants.py`
  is genuinely Data-only; no cross-module reach into another module's private (`_`-prefixed)
  symbols; no import of `api/**`/`webui/**` anywhere in the probe suite.
