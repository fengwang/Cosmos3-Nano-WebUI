# Session 7 Failure Arbiter

Session: MIG-S7. Classify each failure before any fix (per
`docs/agent_workflow/prompts/failure_arbiter.md`).

## FA-1 — X-1: enabling `COSMOS3_API_KEY` 401s the WebUI→API proxy

**Failing behavior / command.** With `COSMOS3_API_KEY` set, requests through the WebUI
BFF are rejected `401` by the API. Root cause: the API enforces the `X-API-Key` header
(`api/app/auth.py:37,44`) while the WebUI BFF injected `Authorization: Bearer <key>`
(`webui/lib/proxy.ts:37`). Surfaced by the `MIG-S6` handoff (pre-existing).

**Category: BUG.** The implementation violated a clear contract clause: the API's auth
module documents and enforces `X-API-Key`, and the deployment's stated capability
("set `COSMOS3_API_KEY` to require the key") could not work because the client sent a
header the API never checks.

**Why not the others.**
- *SPEC_GAP:* no — the required behavior is defined (the API's `X-API-Key` contract).
- *AMBIGUITY:* no — there is a single correct header; the client was simply wrong.
- *ENVIRONMENT:* no — it reproduces deterministically in unit tests.
- *TEST_BUG:* no — the prior tests asserted the buggy `Bearer` behavior; they were
  updated to the contract, which is the fix, not a test hack.

**Allowed next action.** Fix the client toward the API's contract header
(`webui/lib/proxy.ts` → `X-API-Key`) and keep a regression test. Owner approved the
blast-radius amendment (S7-A1) to touch these three WebUI files. Preserve `INV-9` (the
API request shape is unchanged).

**Forbidden next action.** Do not change `api/app/auth.py` (the public `X-API-Key`
contract) or broaden the server to accept `Bearer`; do not touch any other `webui/**`
file.

**Resolution.** `webui/lib/proxy.ts` now sets `x-api-key`; `proxy.test.ts` /
`proxyFetch.test.ts` assert it (plus a client-spoof-overwrite regression). `pnpm
build`/`lint`/`typecheck` pass; vitest 209 passed.

## FA-2 — Forbidden-claims scan matches pre-existing docs across the whole tree

**Failing behavior / command.**
`rg -n "production-ready|guaranteed|always|official" README.md docs` (the contract's
deterministic check) returns matches in files **outside** the S7 blast radius:
`docs/prd.md` ("not production-ready", a negation), `docs/handoff.md` /
`docs/session_6/**` / `docs/session_5/local_checks.md` (casual English such as
"always-heavy", "always-on", "always build first"), and the check definitions
themselves in `docs/session_7.md` / `docs/session_7_contract.yaml`.

**Category: AMBIGUITY.** The check permits two readings: (a) a literal "zero matches
anywhere under `docs`", or (b) the acceptance criterion it encodes — "Claim review finds
no unsupported production or performance claims." Reading (a) is unsatisfiable without
editing files outside the S7 radius (e.g. `prd.md`, `session_6/**`) and would even
require deleting the check's own definition text.

**Why not the others.**
- *BUG:* no product/spec behavior is wrong; this is about interpreting a doc-lint check.
- *SPEC_GAP:* the acceptance criterion is defined ("no unsupported production or
  performance claims"); only the lexical proxy is over-broad.
- *ENVIRONMENT / TEST_BUG:* not a flaky dependency or a test asserting internals.

**Chosen interpretation (b).** Enforce the criterion over the **S7 deliverables**
(`README.md`, the new hygiene files, `docs/session_7/**`, and the evidence/risk edits):
each match must be reviewed and none may function as an unsupported production or
performance claim. Pre-existing whole-tree matches are left untouched (outside the
blast radius; contract change-control).

**Allowed next action.** Keep the S7 deliverables free of these tokens *as claims*.
Verified: `rg … README.md` → none; `docs/release_checklist.md` → none; the only matches
in the new surface are (i) the check's own regex quoted in `docs/session_7/**` and this
file (meta, not claims) and (ii) the standard Contributor Covenant text in
`CODE_OF_CONDUCT.md` ("officially representing", "official e-mail address") — a root
file not under the `README.md docs` scan path and not a product/performance claim.

**Forbidden next action.** Do not edit out-of-radius files (`prd.md`, `session_5/**`,
`session_6/**`, `handoff.md` prose) to satisfy a literal whole-tree zero-match reading.
Recorded as an eval seed (`docs/eval_corpus/mig_s7_forbidden_claims_scope.md`).
