# Eval Harvest — UX-S4 (README / Docs Friendliness)

Date: 2026-07-16
Session outcome: GATE-UX-S4-DOCS **PASS**. Deterministic checks green
(link resolver + both `rg` sweeps + spec-derived asserts); WebUI suite green after
the copy-only `layout.tsx` edit (42 files / 214 tests); 6-axis sharded review
found **1 High + 2 Medium (all fixed)**; fresh-context adversarial verifier PASS.
Docs-only + one allowed metadata copy fix.

Reusable workflow lessons, each with a proposed promotion target.

## 1. A "why" claim in user docs must trace to an evidence row — cross-check causal statements, not just links/tokens (the High)
- **What (BUG, caught by sharded review):** the drafted Status & security /
  SECURITY.md callout said guardrails are off "**(required for the 720p video
  default to fit 32 GB)**". The project's own `docs/evidence_map.md` refutes it:
  E-17 shows the 32 GB fit comes from `--enable-layerwise-offload` +
  `--vae-use-tiling` + `shm_size 16gb` (peak 14,665 MiB), and E-19 +
  `deploy/docker-compose.fp8.yml:18` say `--no-guardrails` is used because
  `cosmos_guardrail` is **not bundled** (guardrails-on would *crash*, not OOM).
- **How caught:** the readability/performance reviewer cross-checked the causal
  clause against E-17/E-19 and the shipped compose comment — not something a link
  or token sweep sees. Fixed to the honest reason before the adversarial pass.
- **Promotion target — update REVIEW.md / adversarial-verifier guidance:** for
  user-facing docs, every *causal/quantitative* claim ("X is required for Y",
  "peaks at N GB", "prefer A over B because …") must cite or match an evidence
  row; a reviewer should attack the *justification*, not just verify the link
  resolves. Honesty defects hide in the "why", which passes both `rg` sweeps.

## 2. Deterministic sweeps don't catch a dropped step or a per-mode over-claim (coverage gap)
- **What (SPEC_GAP, informational):** the contract's deterministic checks are two
  `rg` sweeps + a relative-link resolver. None would catch (a) a removed
  `make build` / checkpoint-download step in the quickstart, or (b) a Features
  cell flipped from "GPU gate" to "GPU-verified" ahead of the evidence map — the
  two highest-value adversarial cases. They were covered here only by human +
  adversarial review.
- **How caught:** the correctness/tests reviewer noted the gap explicitly.
- **Promotion target — add CI/static-analysis check (doc-lint):** a tiny committed
  script asserting (i) the quickstart contains the essential commands
  (`git clone`, `hf download`, `make build`, `make up-fp8`, `make health`, the UI
  URL) and (ii) any Features row marked "verified" is a subset of the evidence
  map's verified modes. Closes the gap the sweeps leave.

## 3. The `rtk` proxy prints a false "JSON parse failed: EOF" on a clean ESLint run (ENVIRONMENT)
- **What:** `pnpm lint` (→ `eslint .`) through the `rtk` token proxy emitted
  "ESLint output (JSON parse failed: EOF while parsing a value…)" with a blank
  exit code. ESLint prints nothing and exits 0 when there are no findings; the
  proxy tried to parse the empty output as JSON.
- **How caught:** re-ran via `rtk proxy pnpm lint; echo $?` → `LINT EXIT=0`,
  empty output = clean.
- **Promotion target — add eval seed / update AGENTS.md:** a `rtk`-proxied linter
  "JSON parse failed: EOF" on empty output is a clean result, not a failure;
  confirm the raw exit code before classifying it as a lint break (ENVIRONMENT).

## 4. When CONTRIBUTING already owns dev/CI, "relocate" means de-duplicate — verify nothing is lost (adversarial case)
- **What (design signal that worked):** the contract's failure mode was
  "CONTRIBUTING duplicating rather than owning" and the adversarial case was "a
  relocated section deleted from README but never added to CONTRIBUTING (lost, not
  moved)". Inspection showed `CONTRIBUTING.md` was already a **superset** of the
  README dev block (it even had `pnpm gen:api`), so the correct move was to delete
  the README duplicate and leave a pointer — then prove all 10 commands still live
  in CONTRIBUTING.
- **Promotion target — keep (review pattern):** before "moving" a section, diff
  the source against the destination; if the destination already contains it, the
  edit is a deletion + pointer, and the check is "enumerate each item and confirm
  it survives in the owner file", not "copy it over".

## 5. In-page anchor slugs with `&` are a resolver false-positive to pre-empt
- **What:** `[Status & security](#status--security)` looks dangling to a naive
  slugger, but GitHub drops `&` between two spaces → a **double** hyphen, so the
  anchor is correct. Both the readability reviewer and the adversarial verifier
  independently flagged then ruled it out.
- **Promotion target — keep (checker note):** a doc-link checker should either
  implement the real GitHub slug algorithm or skip `#` anchors (the session
  checker skips them and the anchors were verified by hand + reviewers), to avoid
  a recurring false positive on `&`-containing headings.

## 6. Process signals that worked (keep)
- Front-loading the three real decisions (verify depth; tone/caveat placement;
  drop-vs-repoint links) into the interview with an explicit restate + yes meant
  the refining pack and edits had no open questions.
- Writing the deterministic checker **first** (RED baseline: it flagged the
  genuinely broken `docs/release_checklist.md` link) gave a concrete red→green
  signal for a docs session, not just a narrative claim.
- Choosing the **full treatment** for a low-risk session (owner decision) is what
  surfaced the §1 honesty defect — the highest-value finding of the session.
