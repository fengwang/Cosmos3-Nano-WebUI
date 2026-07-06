# Session 5 - CPU-Only CI and Test Stabilization

Contract: `docs/session_5_contract.yaml`
Risk: medium
Routing: worker_plus_reviewers

## Objective

Add and stabilize GitHub Actions for CPU-only public checks: Python lint/tests,
WebUI lint/typecheck/unit tests, schema checks, and Docker/Compose rendering.

## Why This Session Exists

The public beta needs a reliable quality gate that runs without model weights,
CUDA, private network access, or self-hosted runners. GPU checks remain manual,
but CPU CI should catch schema drift, UI regressions, import errors, and public
configuration mistakes.

## In Scope

1. Add GitHub Actions workflows for Python and WebUI checks.
2. Install dependencies from public package sources and lockfiles.
3. Verify generated OpenAPI/client types stay in sync.
4. Run unit tests that do not require model weights or CUDA.
5. Add render-only Docker/Compose checks if Docker files exist by this session.
6. Mark GPU tests with explicit skip markers or separate manual commands.
7. Document required local check commands.

## Out of Scope

- No GPU CI.
- No Docker image publishing.
- No secrets or registry credentials.
- No runtime checkpoint inference.

## Deliverables

- `.github/workflows/**` CPU workflows.
- Updated test markers or skip policy.
- CI check evidence and failure classifications.
- Developer check command list.

## Deterministic Checks

```bash
rtk pytest -q
rtk ruff check api tests
rtk proxy sh -lc 'cd webui && pnpm install --frozen-lockfile && pnpm lint && pnpm typecheck && pnpm test'
rtk proxy sh -lc 'cd webui && pnpm gen:api && git diff --exit-code lib/api/schema.d.ts'
```

## Exit Criteria

- `GATE-MIG-S5-CI` passes.
- GitHub Actions run without private resources.
- CPU test failures are either fixed or classified with owner acceptance.
- GPU-only tests cannot accidentally fail CPU CI.

## Handoff

Hand off workflow names, local commands, known skips, and CI gaps to `MIG-S6` and
`MIG-S8`.

