# Session 7 Adversarial Verification

Session: MIG-S7 · Gate: `GATE-MIG-S7-PUBLIC`
Method: fresh-context verifier (no access to the implementation conversation). Saw only
`docs/session_7_contract.yaml`, `docs/project_contract.md`, the evidence map/risk register,
and the diff `0f5d0bb..HEAD`; re-derived every claim from its own commands (41 tool calls).
Prompt: `docs/agent_workflow/prompts/adversarial_verifier.md`. Given an explicit
anti-injection instruction (see the sharded-review injection incident).

## Verdict: PASS

The verifier could not falsify the done condition. No disproven claims; no unsupported
claims.

## Acceptance criteria (verified by command)

- `README.md` non-empty (190 lines); `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, issue/PR templates, `docs/release_checklist.md` exist and are tracked.
- `uv run python tests/test_private_ref_scan.py` → clean (0 findings), exit 0.
- Claim review: `rg "production-ready|guaranteed|always|official" README.md` → **zero** matches.

## Invariants (verified)

- **INV-1:** scan clean; the only email is the intended public maintainer contact (not
  matched by any private-ref pattern).
- **INV-2:** `.gitignore` excludes `models/` + weight/media globs; `misc/logo.png` stays tracked.
- **INV-7:** `LICENSE` scopes MIT to repo code and names weights `openmdw-1.0`/`other`; README
  restates the three-way split.
- **INV-9:** `git diff 0f5d0bb..HEAD -- api/ schemas/openapi.json` is **empty**;
  `api/app/auth.py` `X-API-Key` enforcement unchanged.
- **INV-10:** dependency manifests (`pyproject.toml`, `uv.lock`, `package.json`,
  `pnpm-lock.yaml`) unchanged.
- **Blast radius:** all 30 changed files within `allowed_files` (incl. S7-A1/S7-A2).

## Adversarial cases — all REFUTED

| Case | Result |
|---|---|
| (a) README claims GPU support shipped without evidence | REFUTED — banner "not yet verified"; every mode marked GPU-unverified. |
| (b) MIT LICENSE appears to cover HF weights | REFUTED — `LICENSE` explicitly excludes weights. |
| (c) Quickstart depends on unpublished/registry image or private path | REFUTED — clone + public `huggingface-cli` + local `make build/up`; README says images are not published. |
| (d) Security reporting asks for public-issue disclosure | REFUTED — `SECURITY.md` + `config.yml` forbid it; `blank_issues_enabled:false`. |
| (e) X-1 alters public API shape / leaks / spoofs the key | REFUTED — API diff empty (INV-9); key server-side only; `set` overwrites client value. |
| (f) Private path/host/secret leaked | REFUTED — scan clean; diff grep hits are "do-not-paste" guidance + the public email. |
| (g) `.gitignore` newly ignores a tracked file | REFUTED — `git ls-files \| git check-ignore --stdin` empty; `misc/logo.png` tracked. |
| (h) A forbidden-claims token functions as a real claim | REFUTED — README has zero; other matches are CoC boilerplate / casual English / negation / check definitions. |
| (i) A README relative link does not resolve | REFUTED — all 10 relative targets + logo tracked; anchors match headings. |

## X-1 counterfactual

Reverting `webui/lib/proxy.ts` to `Authorization: Bearer` would fail `proxy.test.ts:39-40`
(`x-api-key === "secret"` and `authorization === null`), the spoof-overwrite test
(`:49-52`), and `proxyFetch.test.ts:47`. Current run: 10/10 targeted, **209 passed** full.

## Strongest counterexample attempted

The whole-tree `rg` forbidden-claims scan returns many matches (superficially a failing
gate). On classification every match is CoC boilerplate, casual English, a negation
(`prd.md` "not production-ready"), or the check's own regex — none in `README.md`, none a
production/performance claim. Does not survive inspection; consistent with `failure_arbiter.md`
FA-2.

## Checks not run (correctly out of scope)

GPU inference and the vLLM-Omni image build (the `MIG-S8` manual gate). The CI badge and
`security/policy`/`discussions` links resolve only after the repo is published (at-publish
item in `docs/release_checklist.md`).
