# Eval Seed - MIG-S6 A Repo-Root .env Is Ignored When Compose Files Live in a Subdir

Session: MIG-S6
Caught by: sharded review (correctness axis)
Severity caught: High (operator config, incl. the API key, silently dropped)

## Prompt Seed

When Compose files live in a subdirectory and are invoked as `docker compose -f
deploy/docker-compose.fp8.yml …`, Compose's **project directory is `deploy/`** (the first
`-f` file's dir), so it auto-loads `deploy/.env` — NOT a repo-root `.env`. A `.env.example`
at the repo root that says "copy to `.env`" then produces a file Compose silently ignores:
`${VAR:-default}` interpolation falls back to defaults, so ports, checkpoint mounts, and
`COSMOS3_API_KEY` are dropped and the API comes up with **auth disabled** — while
`docker compose config` still renders exit 0 (defaults apply), so the deterministic render
check does not catch it.

## Inputs

- `deploy/docker-compose.*.yml` (relative `..` build context + `../models` binds assume
  project dir = `deploy/`)
- `.env.example` at the repo root; `Makefile` wrapping `docker compose -f deploy/...`

## Expected Verifier Behavior

1. Create a repo-root `.env` with `WEBUI_PORT=31337` and `COSMOS3_API_KEY=testkey`.
2. Run `docker compose -f deploy/docker-compose.fp8.yml config` (no `--env-file`) and
   observe the port/key are IGNORED (defaults rendered).
3. Fix so the documented path honors the repo-root `.env`: pass `--env-file .env` (the
   `Makefile` auto-detects it via `$(wildcard .env)`), or document `deploy/.env`, or
   `--project-directory`.
4. Re-render and observe `31337` / `testkey` applied.

## Regression Command Shape

```bash
printf 'WEBUI_PORT=31337\nCOSMOS3_API_KEY=testkey\n' > .env
make config-fp8 | grep -E '31337|testkey'   # must show BOTH after the fix
rm -f .env
```

## Expected Result

A repo-root `.env` is honored by the documented commands; `.env.example` states where the
file must live and how direct `docker compose` invocations pick it up.

## Promotion Target

- Project contract template "Build And Test" note: when compose files live in a subdir,
  either invoke with `--env-file`/`--project-directory` or place `.env` in that subdir;
  document it, because a render check passes on defaults and masks the drop.
- Sharded-review (correctness) check for any subdir-compose layout.
