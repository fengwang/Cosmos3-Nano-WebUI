# GPU-S1 Sharded Review

5 independent read-only reviewers (correctness, security/safety, tests,
architecture, performance) against `git diff phase-2...GPU-S1`, per
`docs/agent_workflow/prompts/sharded_review.md`. Findings below are
deduplicated across reviewers; severity is my own synthesis judgment where
it differs from an individual reviewer's label, with the reason stated.

## Findings

### F1 — Session contract's blast radius omits mandated session-close paths
- **Severity:** High (reclassified up from the architecture reviewer's
  "Medium" — this is a certain, concrete future contract violation if the
  session-close step proceeds unmodified, not a stylistic nit).
- **Reviewers:** Architecture (1).
- **Evidence:** `docs/session_1_contract.yaml`'s `blast_radius.allowed_files`
  lists only `deploy/vllm-omni.Dockerfile`, `deploy/docker-compose*.yml`,
  `deploy/docker-compose.local-image.yml`, `docs/session_1/**`,
  `docs/release_checklist.md`, `docs/evidence_map.md`,
  `docs/risk_register.md`. It does not list `docs/handoff.md` or
  `docs/eval_corpus/**`/`docs/eval_seed_cases.md` — yet this project's own
  CLAUDE.md Session End Protocol mandates writing both, and this session's
  own `docs/session_1/execution_contract.md`, `tasks.md`, and `plan.md` all
  planned to do so. Sibling contracts (`docs/session_2_contract.yaml`,
  `docs/session_3_contract.yaml`, and Phase-1's archived `session_1`/`session_8`
  contracts) all include `docs/eval_seed_cases.md`/`docs/handoff.md`
  explicitly — `GPU-S1`'s contract appears to have simply omitted them when
  drafted.
- **Violated clause:** `project_contract.md` §6 ("Do not edit outside a
  session contract's `blast_radius.allowed_files`"); `AGENTS.md` Boundaries.
- **Impact:** Session close cannot proceed as planned without either
  violating the contract or skipping a CLAUDE.md-mandated deliverable.
- **Smallest safe fix:** Resolved out-of-band with the owner before
  executing session close — see the AMBIGUITY resolution below, not deferred
  as a routine finding.
- **Confidence:** High.

### F2 — Guardrails-on generation path has never been proven to complete a request
- **Severity:** Medium.
- **Reviewers:** Correctness (1), Tests (1) — 2 independent reviewers.
- **Evidence:** Every T2I success in this session's evidence
  (`gate_record.md` Steps 3-4) used an explicit `--no-guardrails` override.
  The bare, guardrails-on default (the shipped `CMD`) has only ever been
  observed to crash (`failure_arbiter.md` FA-5) — never to actually
  complete a generation. This is a pre-existing, credential-blocked
  limitation (not introduced by this session, not fixable in it), but it
  wasn't captured as an explicit tracked risk the way `R-01`/`R-09` were.
- **Violated clause:** `session_1_contract.yaml` `failure_modes_to_watch`
  ("`--no-guardrails` vs guardrails-on paths behave differently and only
  one is tested").
- **Impact:** Low practical impact (disclosed, access-blocked, not this
  session's job to fix) but should be tracked, not just narrated in prose.
- **Smallest safe fix:** Add a `risk_register.md` row (documentation-only)
  noting the guardrails-on path is unverified pending gated-model/`HF_TOKEN`
  provisioning.
- **Confidence:** High that the gap exists; not fixed in this pass per the
  Medium-severity fix policy — noted here for the handoff.

### F3 — Layer-diff provenance check has a `COPY --from=` blind spot
- **Severity:** Medium.
- **Reviewers:** Tests (1), with corroborating evidence quality concerns
  from Correctness (1) — 2 independent reviewers on related aspects.
- **Evidence:** `docs/session_1/gate_record.md`'s cosmos3-layer-reuse check
  compares `RootFS.Layers` sets. That method would produce a **false PASS**
  against a hypothetical `COPY --from=vllm/vllm-omni:cosmos3 ...`
  instruction, since `COPY --from=` repackages content into a new layer
  with a different diffID. No complementary textual check (`grep`/`rg` for
  `cosmos3` across the Dockerfile/compose files) was ever run, even though
  `docs/session_1/specs/vllm-omni-docker-build.md` already specifies that
  exact scenario.
- **Violated clause:** `session_1_contract.yaml` adversarial case ("The
  build appears to succeed but actually reused a cached prebuilt cosmos3
  layer").
- **Impact:** The underlying substance is still sound here (this
  Dockerfile has no `COPY --from=` at all — confirmed by inspection), but
  the check as recorded doesn't itself rule out that adversarial case
  class as rigorously as the spec calls for.
- **Smallest safe fix:** Not applied in this pass (Medium); recommended
  follow-up: `rg -i cosmos3 deploy/vllm-omni.Dockerfile deploy/docker-compose*.yml`
  (excluding this repo's own `cosmos3-nano-*:local` tags), recorded once.
- **Confidence:** High.

### F4 — "No Baked Weights" spec scenario never executed
- **Severity:** Medium.
- **Reviewers:** Correctness (1), Tests (1) — 2 independent reviewers.
- **Evidence:** `docs/session_1/specs/vllm-omni-docker-build.md`'s "No
  Cosmos3 checkpoint files in the image" scenario has no corresponding
  entry anywhere in `gate_record.md`. The Dockerfile has no `COPY`/`ADD`
  from the build context, so the underlying risk is assessed as negligible
  by both reviewers independently — but the scenario itself was never
  actually exercised.
- **Violated clause:** `session_1_contract.yaml` invariant "The image never
  bakes model weights" (INV-2), evidentially rather than substantively.
- **Impact:** Low real risk, real evidence gap.
- **Smallest safe fix:** Not applied in this pass (Medium); recommended
  follow-up: `docker run --rm --entrypoint find cosmos3-nano-vllm-omni:local
  / -xdev -iname "*.safetensors" -o -iname "diffusion_pytorch_model*"`
  (excluding `/models/checkpoint`), recorded once.
- **Confidence:** High.

### F5 — Untested `pip install` fallback branch (no `uv`)
- **Severity:** Medium.
- **Reviewers:** Correctness (1, Low), Tests (1, Medium with a concrete
  fix) — 2 independent reviewers.
- **Evidence:** `deploy/vllm-omni.Dockerfile`'s `else pip install
  --no-cache-dir ...` branch has never run in any build this session
  performed (`uv` was always present). It's reachable via the documented
  `ARG BASE_IMAGE` override, not dead code. If a future base image lacks
  both `uv` and a non-externally-managed Python, this branch could
  reintroduce the exact PEP-668 bug class this session exists to fix,
  silently, the first time it's ever exercised.
- **Violated clause:** None explicit; relates to
  `failure_modes_to_watch`/regression-prevention intent.
- **Impact:** Latent, build-time-loud (not silent-corruption) risk, only on
  a future base-image change nobody has made yet.
- **Smallest safe fix:** Not applied in this pass (Medium); recommended
  follow-up: add `--break-system-packages` (or
  `PIP_BREAK_SYSTEM_PACKAGES=1`) to the fallback line defensively.
- **Confidence:** High that it's untested; Medium that it would actually
  fail on some future base.

### F6 — "Behaviorally equivalent" overstates the `/v1/models` verification method
- **Severity:** Medium.
- **Reviewers:** Architecture (1), with strong concrete technical evidence.
- **Evidence:** `docs/session_1/gate_record.md` states that verifying
  `/v1/models` via `docker exec <container> curl` against the container's
  own loopback is "behaviorally equivalent" to the contract's `curl
  localhost:8000` check. It proves the server process is healthy, but not
  cross-container bridge-network reachability — the actual path `api` uses
  in production (`http://vllm-omni:8000`, per `docker-compose.base.yml`).
- **Violated clause:** Evidentiary rigor implied by INV-8; the spec text in
  `docs/session_1/specs/vllm-omni-serve-entrypoint.md` still says the bare
  `curl -sf http://localhost:8000/v1/models` form.
- **Impact:** Real wording overstatement; low real risk (the underlying
  Compose networking is pre-existing and unchanged by this diff).
- **Smallest safe fix:** Not applied in this pass (Medium); recommended
  follow-up: reword to state plainly what was and wasn't verified, and/or
  add one cross-container probe, or explicitly defer full-stack
  reachability confirmation to `GPU-S3`.
- **Confidence:** High.

### F7 — No CPU-only static regression test for the 3 historical Dockerfile bugs
- **Severity:** Medium, explicitly scoped by the reviewer as a
  forward recommendation, not a GPU-S1 defect (`tests/**` is outside this
  session's blast radius).
- **Reviewers:** Tests (1).
- **Evidence:** This project already has precedent for cheap, CPU-only,
  string-level regression scanners (`tests/test_private_ref_scan.py`,
  already wired into CI). Nothing analogous guards against
  `--break-system-packages`, the old wrong CMD, or `--no-guardrails`
  creeping back into the Dockerfile.
- **Impact:** Real gap relative to project precedent; correctly identified
  as out of this session's authority to fix.
- **Smallest safe fix:** Deferred to a future session with `tests/**` in
  scope — carried to the handoff.
- **Confidence:** High.

### Low/Nit findings (recorded, not fixed — below the Medium fix threshold)
- `deploy/vllm-omni.Dockerfile`: `SETUPTOOLS_SCM_PRETEND_VERSION` is a
  global `ENV`, not the package-scoped
  `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_VLLM_OMNI` variant the same
  `vcs_versioning` package supports (Correctness, Low, verified against
  actual package source).
- `docs/session_1/proposal.md` names the removed capability
  `local-image-override`; its own spec file is
  `local-image-override-disposition.md` (Architecture, Low).
- `docs/session_1/specs/vllm-omni-docker-build.md`'s "Build Toolchain
  Availability" scenario's evidence (a successful build) doesn't actually
  discriminate whether a compiler toolchain was ever invoked (Tests, Low).
- `docs/session_1/gate_record.md` never records the ~22.4 GB GPU memory
  figure observed live during the session (via `nvidia-smi`) despite it
  being available (Performance reviewer noted this as an unverifiable
  premise rather than a finding against the Dockerfile itself).

## No-Findings Axes

- **Security/safety:** no findings. Verified: no secrets/private paths
  (the `/data/models/...` path is a pre-existing, publicly documented mount
  convention, not a private path under INV-1); no weights/media committed;
  SHA pin exact and non-injectable; guardrails-on default confirmed in the
  committed `CMD`; no dangling reference to the deleted compose file; zero
  touches to forbidden files; no privilege/socket changes.
- **Performance:** no findings. Layer ordering, cache-busting boundaries,
  `--no-cache-dir` usage, and the multi-stage-build rejection were all
  independently verified sound.

## Disposition

Per the session's fix policy (Critical/High only, then re-check): **F1** is
the only finding treated as blocking, because it is a certain future
contract violation rather than a quality judgment call — see
`docs/session_1/failure_arbiter.md` FA-6 for its resolution. F2-F7 and the
Low/Nit items are recorded here for the permanent record and carried into
`docs/handoff.md`'s Next Priority Queue / Warnings, not fixed in this
session.
