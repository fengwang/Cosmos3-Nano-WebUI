# Session 6 Failure Arbiter

Session: MIG-S6
Policy: classify every failed check before fixing (BUG / SPEC_GAP / AMBIGUITY /
ENVIRONMENT / TEST_BUG). Ref: `docs/agent_workflow/prompts/failure_arbiter.md`.

## FA-1 — Committed private-reference scanner flagged `/mnt/weights` examples

**Check that failed.** `uv run python tests/test_private_ref_scan.py` (the S5 committed
gate) → 2 findings:
```
docs/session_6/specs/external_checkpoint_mounts.md:24: [mnt_path] /mnt/weights
docs/session_6/specs/external_checkpoint_mounts.md:25: [mnt_path] /mnt/weights
```
The same `/mnt/weights/fp8` example also sat in `.env.example` (outside the scanner's
`SCAN_ROOTS`, but inside the contract's `rg … deploy docs .env.example` surface).

**Classification: BUG (in the new session docs).** The scanner enforces the
S1/S5 sanctioned-placeholder convention: the only allowed absolute-path prefix is
`/path/to/` (`ALLOWED_PLACEHOLDER_PREFIXES`), and `mnt_path` (`/mnt/[…]`) is a
private-path heuristic (INV-1). The failure is not a scanner defect and not an
environment issue — the new spec/`.env.example` introduced a non-sanctioned absolute
example the gate correctly rejects. The scanner is out of the S6 blast radius
(`tests/**`) and is the established enforcement mechanism, so it is **not** modified.

**Smallest safe fix (in blast radius).** Replace the `/mnt/weights/fp8` examples with
the sanctioned `/path/to/fp8-weights` placeholder in both
`docs/session_6/specs/external_checkpoint_mounts.md` and `.env.example`. The override
scenario stays verifiable: `COSMOS3_FP8_DIR=/path/to/fp8-weights docker compose -f
deploy/docker-compose.fp8.yml config` renders `source: /path/to/fp8-weights`.

**Post-fix evidence.** `tests/test_private_ref_scan.py` → **clean (0 findings)**; the
contract path-pattern `rg` over `deploy .env.example Makefile .dockerignore
docs/session_6` → **no match**; the override render confirmed.

**Observation handed to MIG-S7/S8 (not fixed here).** The `mnt_path` heuristic flags
*any* `/mnt/…`, including legitimate generic mount examples. README/hygiene work
(`MIG-S7`, which owns the scanner's home and public docs) must use `/path/to/…` or
repo-relative examples for mount paths, or widen `ALLOWED_PLACEHOLDER_PREFIXES` with an
explicit owner decision. No change made in S6.

## Notes on non-failures (classified, no code change)

- **vLLM-Omni image build not run.** Deferred by design (heavy/GPU) to the `MIG-S8`
  gate; it is not a S6 deterministic build check (contract acceptance: "Dockerfiles
  build from public inputs **or failures are classified**"). Category: ENVIRONMENT/
  scope — recorded, not a fix.
- **Rendered config embeds the invoking CWD absolute path** (e.g. the repo root under
  `context:`/`source:`). This is normal Docker relative-path resolution; the
  **committed** files use `..`/`../models` placeholders (scan-clean). Not a finding.
