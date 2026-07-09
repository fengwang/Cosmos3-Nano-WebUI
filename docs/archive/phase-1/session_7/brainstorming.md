# Session 7 Brainstorming - README, Project Hygiene, and Beta Polish

Date: 2026-07-07
Session: MIG-S7
Risk: medium · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S7-PUBLIC`
Status: approved (owner, 2026-07-07)

## Context explored

- The public repo is a curated migration (`MIG-S1`..`MIG-S6`). `README.md` exists but
  is **0 bytes**; `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md` are absent. `misc/logo.png`
  (123 KB) is tracked. `references/readme.howto.md` is **gitignored** (local guidance only,
  not public) and informs structure/tone.
- The authoritative checkpoint facts already live in the tracked, public
  `docs/model_setup.md` (repo IDs, pinned revisions, licenses, env surface, per-mode
  matrix, drift caveats). The README should **link** to it, not duplicate it.
- App surface to describe accurately (from the imported source):
  - Generation (async job, `202`→`Job`): `POST /v1/generation/{t2i,t2v,i2v,t2v_audio}`.
  - Action (async): `POST /v1/action/{forward_dynamics,inverse_dynamics,policy}`.
  - Reasoning: `POST /v1/reason`.
  - Jobs + SSE: `POST /v1/jobs`, `GET /v1/jobs/{id}`, `.../events` (SSE),
    `.../artifact`, `.../trajectory`, `POST .../cancel`.
  - Health: `GET /v1/health/{live,ready}`; metrics: `GET /v1/metrics` (Prometheus,
    excluded from the OpenAPI schema).
  - WebUI: Next.js 15 / React 19 / TanStack Query / three.js (`pnpm`).
  - Python 3.12 (`>=3.12,<3.13`), `uv`; local-build Docker/Compose (fp8/nvfp4 + reasoning
    overlay) via `Makefile`; CPU-only CI at `.github/workflows/ci.yml`.
- Public remote is a seed (`origin/main` = `c3983f7 initialize repo`); `session-7` is
  **not pushed**. Prior sessions committed locally per session.

## Evidence discipline (dominant constraint)

Everything runtime — FP8, NVFP4, RTX 5090, generation, reasoning, action — is
**GPU-unverified**. Per `INV-6`/`INV-8` and the evidence map, GPU inference is the
`MIG-S8` manual gate. Drift **D1** (`docs/session_4/drift_report.md`): the in-process
`diffusers_oracle`/`diffusers_action` engines cannot load+verify the *current* public
checkpoints as-is; the **default** engine is the `vllm_omni` container path, whose real
compatibility is an S6/S8 gate. Licenses are separate (`INV-7`): repo **MIT**, weights
**`openmdw-1.0`** (FP8/NVFP4), base **`other`** (`nvidia/Cosmos3-Nano`). The README
must be evidence-qualified throughout and make no production/performance claim.

## Clarifying decisions (owner, 2026-07-07)

1. **X-1 auth mismatch** — the prior handoff flags it as an S7 priority, but `api/**` and
   `webui/**` are runtime source (forbidden by the S7 blast radius). **Decision: fix the
   code** via a noted `allowed_files` amendment. **Direction: WebUI → `X-API-Key`** (fix
   the BFF to send the header the API already contracts on; API code untouched;
   preserves `INV-9`).
2. **Hygiene beyond the listed files** — **Decision: add both** `.gitignore` hardening
   **and** `CODE_OF_CONDUCT.md`, via the same noted amendment (owner-reviewed, mirrors
   the S4 FA-4 / S5 D10 / S6 amendment precedent).
3. **Badges** — **Decision: static + CI status badge** (License: MIT · Python 3.12 ·
   Status: beta/research-preview · GitHub Actions CI badge → `ci.yml`). The CI badge
   resolves once the repo is public; noted as an at-publish item.

## X-1 root cause (confirmed by reading the code)

- API (`api/app/auth.py:37,44`) enforces header **`X-API-Key`** (constant-time compare
  against `COSMOS3_API_KEY`), applied to job/artifact routes (`api/app/main.py:211`).
  This is the API's public contract header.
- WebUI BFF (`webui/lib/proxy.ts:37`) injects **`Authorization: Bearer <key>`**
  server-side. The browser never holds the key (BFF-injected — `proxyFetch.test.ts`).
- Result: with `COSMOS3_API_KEY` set, the API sees no matching `X-API-Key` → `401`.
- **Smallest safe fix:** change `webui/lib/proxy.ts:37` to `out.set("x-api-key", apiKey)`
  and update the assertions in `webui/lib/proxy.test.ts` + `webui/lib/proxyFetch.test.ts`.
  `Headers.set()` overwrites any client-supplied `x-api-key`, so the browser cannot spoof
  it. The API request shape is unchanged (`INV-9` preserved / strengthened).

## Approaches considered

### README architecture

- **A1 — Concise README + link to existing public docs (chosen).** Follows the how-to's
  "keep it concise, move detail to docs." Detailed checkpoint facts stay in the already
  public `docs/model_setup.md`; the README carries the pitch, feature matrix, quickstart,
  setup summary, limitations, and troubleshooting. Fits the blast radius (new docs are
  limited to `docs/release_checklist.md` + `docs/session_7/**`).
- **A2 — Everything-inline README (rejected).** Full env tables + full matrices + full
  troubleshooting in one file. Violates "keep concise"; risks the named failure mode
  "README grows too long and hides setup steps"; duplicates `model_setup.md`.
- **A3 — New `docs/` landing page (rejected).** Move detail into new `docs/*.md`. Needs
  extra amendment surface for little gain when `model_setup.md` already covers checkpoints.

### X-1 direction

- **WebUI → `X-API-Key` (chosen).** One line + 2 test files; API untouched; `INV-9` safe.
- **API also accepts `Bearer` (rejected).** Widens the server's accepted auth surface and
  edits server contract code for no benefit over the client-side fix.

## Validated design (high level)

1. **README.md** — logo + badges + one-liner + subtitle; research-preview banner;
   evidence-qualified feature matrix (each mode = *code present / GPU-unverified, S8
   gate*); quickstart (clone → download public HF checkpoints → `make build` + `make
   up-fp8`, local build only, no registry images, no private paths); requirements;
   external checkpoint setup with **license separation** and a link to `docs/model_setup.md`;
   development setup mirroring CI; **Limitations & beta status** (GPU unverified, D1,
   R-16 socket privilege, auth now working when enabled); troubleshooting (compose
   `--env-file`/project-dir, loopback binding, cold-start timeout); Security/Contributing/
   License/CoC links.
2. **Hygiene files** — `LICENSE` (MIT), `SECURITY.md` (private reporting, **not** public
   issues), `CONTRIBUTING.md` (specific commands, mirrors CI, links CoC),
   `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `.github/ISSUE_TEMPLATE/{bug_report,
   feature_request}.yml` + `config.yml` (no sensitive-data fields),
   `.github/PULL_REQUEST_TEMPLATE.md`, `docs/release_checklist.md`.
3. **X-1 fix** — `webui/lib/proxy.ts` sends `X-API-Key`; tests updated (TDD).
4. **`.gitignore` hardening** — ignore `__pycache__/`, `.venv/`, `node_modules/`, build
   and cache dirs, `models/`, media artifacts. Verify no currently-tracked file is newly
   ignored.
5. **Contract amendment** — extend `allowed_files` for the above; record in
   `session_7_contract.yaml`, `failure_arbiter.md`, and the handoff.
6. **Docs** — update `docs/evidence_map.md` + `docs/risk_register.md` (R-01/R-09/R-11/
   R-15/R-16 + X-1 closure).

## Verification approach

- Presence checks; committed private-ref scanner clean over the new surface (README,
  hygiene, `.github/**`, `docs/session_7/**`).
- **Forbidden-claims scan** (`production-ready|guaranteed|always|official`) is a lexical
  heuristic. The contract's real acceptance criterion is "no unsupported production or
  performance claims." Pre-existing whole-tree matches are negations ("not
  production-ready"), casual English ("always-heavy"), or the check definitions
  themselves — all outside the S7 blast radius. Enforce zero matches over **my
  deliverables** (README + hygiene + `docs/session_7/**` + evidence/risk edits) and
  record the interpretation as a Failure-Arbiter AMBIGUITY resolution.
- WebUI `pnpm test` + `lint` + `typecheck` green for the X-1 change.
- Sharded review (5 axes; medium risk) + fresh-context adversarial verifier against the 4
  named adversarial cases.

## Adversarial cases to pre-empt (from the contract)

- "GPU support shipped without evidence" → research-preview banner + per-mode
  *GPU-unverified (S8)* qualifier.
- "MIT covers the HF weights" → explicit three-way license separation.
- "Quickstart depends on unpublished images or private paths" → local `make build` +
  public `huggingface-cli` downloads; no registry; no private/absolute paths.
- "Security reporting asks users to disclose in public issues" → `SECURITY.md` routes to
  GitHub private vulnerability reporting / email and explicitly forbids public issues;
  `config.yml` disables blank issues and points security elsewhere.
