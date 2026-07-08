# Eval Seed - MIG-S5 Next.js typecheck Requires a Prior Build

Session: MIG-S5
Caught by: baseline deterministic check (empirical typecheck-without-build)
Severity caught: Medium (a contract/CI check that cannot pass as written)

## Prompt Seed

A CI or contract check that runs `pnpm typecheck` (`tsc --noEmit`) on a Next.js app
**without a prior `pnpm build`** fails, because Next generates the CSS-module
(`*.module.css`) type declarations and `next-env.d.ts` during the build. The
`session_5_contract.yaml` deterministic check originally listed
`install → lint → typecheck → test` with no build (SPEC_GAP).

## Inputs

- `webui/tsconfig.json` (includes `.next/types/**`; Next TS plugin)
- The WebUI check sequence in the session contract / CI workflow

## Expected Verifier Behavior

1. Run `pnpm typecheck` on a genuinely fresh tree (`rm -rf .next next-env.d.ts`) and
   observe `error TS2307: Cannot find module './X.module.css'`.
2. Run `pnpm build` then `pnpm typecheck` and observe exit 0.
3. Classify the missing build as **SPEC_GAP**; fix by ordering `build` before
   `typecheck` in both the contract check and the workflow (not by weakening typecheck).

## Regression Command Shape

```bash
cd webui && pnpm install --frozen-lockfile
rm -rf .next next-env.d.ts && pnpm typecheck   # FAILS (TS2307 CSS-module)
pnpm build && pnpm typecheck                    # PASSES
```

## Expected Result

typecheck fails pre-build and passes post-build; the contract/CI ordering is
`install → gen:api diff → build → lint → typecheck → test`.

## Promotion Target

Contract/CI-recipe rule: for a Next.js app, `next build` MUST precede `tsc`
typecheck (and generated-type-dependent steps). A check that omits it is a SPEC_GAP,
not a code bug. Candidate for the project contract template's "Build And Test" notes.
