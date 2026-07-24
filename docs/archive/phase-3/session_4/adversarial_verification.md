# UX-S4 Adversarial Verification

Date: 2026-07-16
Verifier: fresh-context, independent (did not write or review the change). Inputs
limited to `docs/session_4_contract.yaml`, `docs/project_contract.md`
(GATE-UX-S4-DOCS), the `git diff HEAD`, and the recorded evidence
(`docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
`docs/model_setup.md`, `Makefile`, `deploy/docker-compose.*.yml`). Mandate: try
to **falsify** that `GATE-UX-S4-DOCS` is satisfied.

## Verdict: PASS

The verifier independently re-ran every deterministic check and cross-checked
every user-facing claim against evidence. No disproven claims; no unsupported
claims.

## What the verifier independently confirmed

- **Blast radius clean.** `git diff --name-only HEAD` = exactly `README.md`,
  `CONTRIBUTING.md`, `SECURITY.md`, `webui/app/layout.tsx`; sole untracked add is
  `docs/session_4/` (allowed). No `api/**`, `deploy/**`, `schemas/**`, `tests/**`,
  other `webui/**`, `.env`, or `docs/archive/**` touched. The allowed evidence
  docs were unchanged at verification time (they are updated in close-out).
- **`rg "release_checklist|R-16" README.md SECURITY.md`** → no matches; the old
  two `docs/release_checklist.md` links and the `SECURITY.md` R-16 pointer are
  gone; R-16 repointed to the live **R-01** (`SECURITY.md:56`).
- **`rg "COSMOS3_API_KEY|X-API-Key|api_key|apiKey"`** → no matches (no auth
  reintroduction; R-09 held).
- **Links/anchors:** using GitHub's real slug algorithm, 0 dangling links and
  0 missing anchors across the three docs. Explicitly ruled out the
  `#status--security` slug (the `&` is dropped between two spaces → double hyphen,
  which matches the heading) as a **false positive**, not a defect.
- **Quickstart runnable:** `git clone` → `hf download …FP8… --revision
  9bf5d6ae164688487bdb71947ccc6ebe70d12900` → `cp .env.example .env` →
  `make build` → `make up-fp8` → `make health` → `http://localhost:3000`, in
  order; all `make` targets exist; the pinned FP8 revision matches
  `model_setup.md`/`eval_seed_cases.md` exactly.
- **Dev/CI moved, not lost:** all 10 dev/CI commands present in `CONTRIBUTING.md`;
  none remain as a command block in `README.md` (its only fenced block is the
  quickstart).
- **Honesty:** VRAM figures (≈14.7 GB FP8 / ≈18.5 GB NVFP4) match E-17/E-18;
  "prefer NVFP4 … FP8 relies on layer-wise offload" matches E-17/E-19 + R-05;
  guardrails-off matches the shipped compose `--no-guardrails` + `cosmos_guardrail`
  not bundled (E-19); loopback + root-equivalent socket match
  `docker-compose.base.yml` + R-01; only t2i is "GPU-verified", other modes are
  "CPU-tested · GPU gate (MIG-S8)" with the 720p t2v smoke explicitly **not**
  promoting them to verified.
- **`layout.tsx`** diff is `metadata.description` + one comment only — no logic,
  JSX, or import change.

## Strongest counterexample considered

The `#status--security` anchor (a naive resolver flags it as dangling). Ruled out
with a precise GitHub slugger — it resolves. Non-defect.

## Failure Arbiter

Not invoked — the verifier returned PASS with no failing check. (The one High +
two Medium findings from the sharded review were fixed **before** this pass; the
verifier re-derived those areas from evidence and found them accurate.)
