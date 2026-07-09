<!--
Thanks for contributing! Please keep PRs focused and read CONTRIBUTING.md.
Do not include secrets, tokens, private paths, or model weights.
-->

## Summary

<!-- What does this PR change, and why? -->

Closes #

## Type of change

- [ ] Bug fix
- [ ] Feature
- [ ] Docs
- [ ] Build / CI / deploy
- [ ] Refactor / chore

## Checks run

<!-- Tick what you ran locally. These mirror CI (.github/workflows/ci.yml). -->

- [ ] `uv run ruff check api tests`
- [ ] `uv run pytest -m "not gpu"`
- [ ] `cd webui && pnpm build && pnpm lint && pnpm typecheck && pnpm test`
- [ ] `pnpm gen:api` + `git diff --exit-code lib/api/schema.d.ts` (if the API schema changed)

## Checklist

- [ ] I staged files explicitly (`git add <path>`), not `git add .`.
- [ ] No secrets, tokens, private paths, or model weights are included.
- [ ] Docs updated if behavior or setup changed (README / `docs/`).
- [ ] If a README/docs claim about runtime behavior changed, evidence in
      `docs/evidence_map.md` was updated (or it is marked as a beta limitation).
- [ ] The public API request/response shape is unchanged, or the change is
      intentional and covered by tests + updated `schemas/openapi.json`.
