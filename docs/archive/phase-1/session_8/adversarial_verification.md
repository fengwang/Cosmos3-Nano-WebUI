# Adversarial Verification - MIG-S8 Release Gate

Date: 2026-07-07 · Verifier: fresh-context subagent (did not write or review the work; saw
only the contracts, the diff `f285299..HEAD`, and the evidence outputs — not the
implementation conversation). Task: **falsify** the claim that `GATE-MIG-S8-BETA` can record an
evidence-based GO recommendation with every PRD MUST covered, claims tied to public evidence,
no unowned release-blocking risk, GPU honestly beta-limited, and docs reconciled.

## Verdict: PASS

The claim survived falsification on all 8 axes; the verifier reproduced every load-bearing
number and structural fact from source/commands.

## Disproven claims

None. Independently reproduced and matched exactly:

| Claim | Independent check | Result |
|---|---|---|
| pytest `-m "not gpu"` = 486 / 0 fail | JUnit `<testsuite tests="486" failures="0" errors="0" skipped="0">` | ✅ |
| vitest = 209 / 39 files | `pnpm test` | ✅ |
| compose fp8/nvfp4 `config` exit 0, 0-byte stderr, 76 lines | ran both | ✅ |
| pins/revisions (vLLM-Omni `697035…`, FP8 `4e181f99…`, NVFP4 `b5c9332e…`, base `fea6e03…`) | traced every mention; no conflict | ✅ |
| `origin/main` = seed `c3983f7` | `git rev-parse origin/main` | ✅ |
| 485 → 486 = +1 test from S8-A2 | scanner test defs 11 (`f285299`) → 12 (HEAD) | ✅ exactly +1 |
| 16 MUSTs, 14 PASS / 2 BETA-LIMITED / 0 NO-GO; FR-9 & NFR-6 the only BETA-LIMITED | per-row verdict extraction | ✅ |
| committed scanner clean | `uv run python tests/test_private_ref_scan.py` → 0 findings | ✅ |

## Independent falsification (all survived)

1. **INV-1 leak scan (whole tree, not just the committed roots/patterns):** the verifier ran
   its own secret scan (hf_/sk-/AKIA/ghp_/github_pat_/private-key/URL-creds) and a wider
   private-path scan (added `/srv/`, `/opt/`, `/workspace/`, `/data/home…` roots) over **all**
   `git ls-files` — **no surviving private path, host, codename, or secret**; no tracked
   weight/media. The `/workspace/…` scrub (S8-A1) holds; the S8-A2 patch fires on a planted
   `/workspace/…` path and correctly ignores the ellipsis form.
2. **Blast radius:** all changed files within `docs/session_8/**` + the 6 reconciled docs + the
   two recorded amendments (`docs/session_{2,3,4}/**`, `tests/test_private_ref_scan.py`).
3. **Adversarial cases / failure modes:** each pre-empted (no-evidence-claim, wrong-revision
   incl. the BF16 base pin, scan-too-narrow, open-blocker; no README/Docker contradiction; GPU
   marked unverified while skipped; GitHub-runner flagged at-publish).
4. **GPU honesty / unowned risk / GO overreach:** no GPU case marked PASS; every risk row leads
   with a disposition + owner; all 8 GO-rule clauses backed by reproduced evidence; the
   recommendation is advisory ("owner ratifies").

## Strongest counterexample (noted, does not break the claim)

The committed scanner's `SCAN_ROOTS = (api, webui, tests, schemas, docs, .github)` does **not**
cover tracked `deploy/**`, `tools/**`, or root files (`README.md`, `.env.example`, `LICENSE`,
`Makefile`, `pyproject.toml`) — so check #12 is clean-by-construction for that surface (the
"scan scoped too narrowly" case at the **root** level, distinct from the pattern-level gap
fixed by S8-A2). Why it does not break the GO: the verifier scanned that blind-spot surface
independently and found it **clean**; check #15b runs a `git ls-files` whole-tree broad scan
that covers the gap; and FA-3 + the scanner docstring document the limitation. **Residual /
follow-up:** extend the scanner's `SCAN_ROOTS` to `deploy`, `tools`, and root files (this
compounds the existing S7 T-1 "durable `deploy/` CI gate" item) — recorded in the handoff and
eval seed `mig_s8_scanner_abspath_blindspot`. Not a beta blocker (surface verified clean now).

## Unsupported claims (immaterial)

- Some S8 outputs cite `docs/handoff.md`, which is still the **MIG-S7** handoff (the S8 handoff
  is task 6.2, produced at close — honestly disclosed in sharded_review R-F6). The specific
  facts those citations rest on (X-1 / `X-API-Key`) are present in it; the literal GPU/build
  commands live in `release_checklist.md` §6/§7 (verified present).
- The public maintainer email `feng.wang1@hexagon.com` also appears in `docs/session_7/plan.md`
  — the intended public contact, not a leak.

## Disposition

PASS with no High/Critical. The one latent gap (scanner root scope) is documented, compensated,
and independently confirmed clean; it is routed as a post-beta scanner/CI improvement, not a
release blocker. No Failure-Arbiter FAIL to classify from this verification.
