# GPU-S1 Failure Arbiter Log

Classified live, during the task loop, before each fix was applied.

## FA-1: `uv pip install` — no virtual environment found

- **Category:** BUG (in this session's own Dockerfile draft).
- **Evidence:** `error: No virtual environment found; run 'uv venv' to create an
  environment, or pass '--system' to install into a non-virtual environment`
  at `deploy/vllm-omni.Dockerfile`'s fork-install `RUN` step, first build
  attempt.
- **Why other categories don't fit:** Not SPEC_GAP/AMBIGUITY — the contract
  doesn't touch this level of detail. Not ENVIRONMENT — the base image is
  exactly as intended (`v0.24.0`, confirmed via the sm_120 probe); this is a
  missing CLI flag in code this session wrote. Not TEST_BUG — no test
  involved.
- **Allowed next action:** add `--system` to the `uv pip install` invocation.
- **Forbidden next action:** switching base image or fork-install mechanism.

## FA-2: fork install fails version resolution (`InvalidVersion: 'dev'`)

- **Category:** BUG, but in the **external** `fengwang/vllm-omni` fork's own
  build backend (`setuptools_scm`/`vcs_versioning`), not in this repository.
- **Evidence:** `vcs_versioning` cannot parse a PEP 440 version from the
  nearest reachable git tag at the pinned commit
  (`cosmos3-nano-webui-mig-s2`, an internal tracking tag, not a version
  string), and its own "pretend version" fallback path also produces an
  unparseable literal `'dev'`. Confirmed by installing `vcs_versioning`
  standalone and reading `_overrides.py` (`PRETEND_KEY =
  "SETUPTOOLS_SCM_PRETEND_VERSION"`).
- **Why other categories don't fit:** Not a bug in this session's code path
  in the sense of "fix the logic" — the logic lives in a repo outside this
  session's (and this project's) blast radius (`project_contract.md` Hard
  Commitment 7: external-repo work is out of this repository's blast
  radius and does not authorize edits to this repository's runtime
  source — the inverse also holds: this session cannot edit the fork to
  fix its own bug). Not ENVIRONMENT — reproducible from a clean pull, not
  flaky. Not SPEC_GAP/AMBIGUITY — the contract only requires the fork
  install to work, not a specific mechanism.
- **Allowed next action:** work around it entirely within
  `deploy/vllm-omni.Dockerfile` via `ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0`
  (a standard, documented `setuptools_scm`/`vcs_versioning` override), with a
  comment explaining why.
- **Forbidden next action:** patching, forking, or vendoring
  `fengwang/vllm-omni` to fix its own version-detection bug (that is
  `GPU-S4`/upstream-contribution territory at most, and this specific bug
  isn't even part of Task C's quant-loader scope).

## FA-3: doubled `vllm serve vllm serve …` (`unrecognized arguments`)

- **Category:** BUG (in this session's own Dockerfile draft).
- **Evidence:** `vllm: error: unrecognized arguments: serve /models/checkpoint`;
  `docker inspect` showed the base image's inherited
  `Entrypoint=["vllm","serve"]` with this session's `CMD` appended after it,
  producing `vllm serve vllm serve /models/checkpoint --omni …`.
- **Why other categories don't fit:** Not ENVIRONMENT — deterministic, same
  every time. Not SPEC_GAP — the contract specifies the exact serve command;
  it just doesn't specify Docker `ENTRYPOINT`/`CMD` mechanics, which is an
  implementation detail this session owns. The fork's own
  `docker/Dockerfile.cuda` already demonstrates the fix (`ENTRYPOINT []`)
  for exactly this reason — this session's draft omitted it.
- **Allowed next action:** add `ENTRYPOINT []` before `CMD`.
- **Forbidden next action:** changing the confirmed serve command's flags to
  work around the doubling instead of clearing the inherited entrypoint.

## FA-4: checkpoint mount appears empty (`does not have model_index.json`)

- **Category:** ENVIRONMENT (operator-invocation gap, not a bug in any
  tracked file).
- **Evidence:** `docker compose -f deploy/docker-compose.fp8.yml run --rm
  --entrypoint python3 vllm-omni -c '...os.listdir("/models/checkpoint")...'`
  returned `[]` when invoked without `--env-file .env`. Compose's project
  directory is `deploy/` (the first `-f` file's directory), so it looked for
  `deploy/.env` and silently ignored the real `.env` at the repo root,
  falling back to `COSMOS3_FP8_DIR`'s default
  (`../models/Cosmos3-Nano-FP8-Blockwise`, i.e. `<repo>/models/...`, which
  does not exist) — Docker auto-created an empty directory for the missing
  bind-mount source rather than erroring. `.env.example`'s own header
  comment already documents the fix: run with `--env-file .env` from the
  repo root (matching the Makefile's `ENV_FILE := $(wildcard .env)` /
  `--env-file` pattern).
- **Why other categories don't fit:** Not a BUG — `deploy/docker-compose*.yml`,
  `.env`, and `.env.example` are all correct as written; this session simply
  didn't pass a flag those files' own documentation already specifies. Not
  SPEC_GAP — `session_1_contract.yaml`'s deterministic-check list omits
  `--env-file .env`, which is a minor gap in that list's literal text, but
  the correct invocation is unambiguously documented elsewhere in this
  repository, so this doesn't rise to a contract ambiguity worth stopping
  the session for.
- **Allowed next action:** always pass `--env-file .env` for any `up`/`run`
  invocation from the repo root; clean up the stray Docker-auto-created
  `<repo>/models/Cosmos3-Nano-FP8-Blockwise` empty directory (never commit
  it).
- **Forbidden next action:** changing the default fallback path in
  `deploy/docker-compose*.yml` to "fix" this, or committing anything under a
  new top-level `models/` directory.

## FA-6: session contract's blast radius omits mandated session-close paths

- **Category:** AMBIGUITY — the session contract and the standing CLAUDE.md
  workflow instructions make conflicting demands, and the contract permits
  no interpretation that satisfies both without an explicit choice.
- **Evidence:** `docs/session_1_contract.yaml`'s `blast_radius.allowed_files`
  does not include `docs/handoff.md` or `docs/eval_corpus/**`/
  `docs/eval_seed_cases.md`. The standing CLAUDE.md Session End Protocol
  mandates writing both. Sibling contracts
  (`docs/session_2_contract.yaml`, `docs/session_3_contract.yaml`, and
  Phase-1's archived `session_1`/`session_8` contracts) all include
  `docs/eval_seed_cases.md`/`docs/handoff.md` explicitly — `GPU-S1`'s
  contract appears to omit them by drafting oversight, not by deliberate
  scope restriction. Caught by the sharded review (F1 in
  `docs/session_1/sharded_review.md`), not by the implementer beforehand.
- **Why other categories don't fit:** Not a BUG — nothing was implemented
  incorrectly. Not SPEC_GAP in the narrow sense (the *contract's* intent
  for the session's core work is clear); the gap is specifically about the
  two universally-needed session-close paths. Not ENVIRONMENT — fully
  reproducible by reading two files side by side. Not TEST_BUG — no test
  involved.
- **Allowed next action:** stop and get the owner's explicit choice before
  writing either path, per `AGENTS.md` Boundaries ("do not edit files
  outside the session contract blast radius without stopping").
- **Forbidden next action:** silently writing `docs/handoff.md` or
  `docs/eval_corpus/**` without flagging the conflict first, and silently
  skipping the CLAUDE.md-mandated session-close deliverables instead.

## FA-5: guardrails hard-fail (`ValueError: You have disabled the safety checker…`)

- **Category:** Not a failure to fix — expected behavior matching the
  design's own guardrails-on-by-default decision, confirmed rather than
  contradicted.
- **Evidence:** `CosmosSafetyChecker.__init__` raises unless
  `cosmos-guardrail`/the gated `nvidia/Cosmos-1.0-Guardrail` model is
  available; neither is provisioned in this environment (no `HF_TOKEN` for
  the gated model), exactly as `docs/model_setup.md` §9 and
  `docs/session_1/design.md` Decision 3 anticipated.
- **Why other categories don't fit:** Not a bug — the shipped `CMD` is
  intentionally guardrails-on; this is the documented cost of that choice,
  not a defect. Not ENVIRONMENT in the "flaky" sense — deterministic, and
  the correct handling was already decided before it was ever hit.
- **Allowed next action:** apply `--no-guardrails` only via an untracked,
  scratch Compose override for this session's own T2I evidence capture,
  documented as a known limitation (per
  `docs/session_1/specs/vllm-omni-serve-entrypoint.md`'s "Guardrails-On
  Default" requirement).
- **Forbidden next action:** adding `--no-guardrails` to the Dockerfile's
  shipped `CMD`.
