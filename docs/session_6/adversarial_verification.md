# Session 6 Adversarial Verification - Local-Build Docker and Compose

Session: MIG-S6 · Gate: `GATE-MIG-S6-DOCKER`
Method: a fresh-context verifier (`docs/agent_workflow/prompts/adversarial_verifier.md`)
that did not write the code or join the review. It saw only the session/project
contracts, the diff (`443f3da..HEAD`), `docs/model_setup.md`, and the baked-in code
contracts, and was told to assume the completion claim is false and falsify it. It
reproduced every check itself on real Docker 29.6.1 / Compose 5.1.4 with no `.env`
present; planted-failure experiments used scratch copies (no committed file modified).

## Verdict: PASS

All 4 acceptance criteria, all 4 contract invariants, all 6 deterministic checks
(including the strict no-unset-variable-warning render requirement), and refutation of
all 4 adversarial cases reproduced independently.

## Independently reproduced evidence

| Check | Result |
|---|---|
| `docker compose -f deploy/docker-compose.fp8.yml config` | exit 0, **0 bytes stderr**, 3 services, `COSMOS3_CHECKPOINT_LABEL: fp8` |
| `…nvfp4.yml config` | exit 0, **0 bytes stderr**, 3 services, label `nvfp4` |
| fp8 + reasoning overlay render | exit 0, 0 bytes stderr |
| weight-copy scan over `deploy/` | no match (clean) |
| `uv run python tests/test_private_ref_scan.py` | clean (0 findings) |
| `docker build -f deploy/api.Dockerfile` (lean) | exit 0; image **torch-free** (`torch: False`), fastapi present, no weight baked |
| `docker build -f deploy/webui.Dockerfile` | exit 0, no weight baked |
| Blast radius (`git diff 443f3da..HEAD --name-only`) | all changed files within `allowed_files`; no violation |

## Adversarial cases — all refuted (verifier tried to prove each TRUE)

- **(a) broad `COPY .` / weight glob bakes weights** → FALSE. Every COPY is narrow
  (`api/`, `webui/`, manifests, cross-stage binaries); the only weight reference is the
  runtime `--model /models/checkpoint` mount target.
- **(b) renders but points at a private/absolute default** → FALSE. Committed defaults
  are `${VAR:-../models/...}`; rendered source is repo-relative `<repo>/models/...`; the
  override `COSMOS3_FP8_DIR=/path/to/fp8-weights` renders that exact source (INV-4).
- **(c) pin is mutable/branch-only** → FALSE. Immutable 40-hex commit
  `697035018b70cef76b974a909d23371a9984c3f2` via public HTTPS.
- **(d) containers only run on a private-network setup** → FALSE. Default Compose bridge;
  ports bind `127.0.0.1` by default with a documented `BIND_ADDR=0.0.0.0` LAN escape.

## Checks have teeth (planted in scratch copies, reverted)

A planted `COPY x.safetensors` / `ADD x.pt` **is** caught by the weight scan; a planted
`/home/<user>/...` **is** caught by the private-reference scanner; a variable without a
`${VAR:-default}` **does** emit a Compose unset-variable warning — so the real stacks'
0-byte stderr is a meaningful pass, not a hollow one.

## Strongest counterexample (does not fail the gate)

The weakest point is coverage, already disclosed as sharded-review **T-1**: the render +
weight-copy gates live only in the `Makefile` (manual), and the committed scanner's
`SCAN_ROOTS` exclude `deploy/`, `.env.example`, and `Makefile`, so nothing in CI durably
guards the new deployment surface against a future private-path or weight-COPY regression.
This is out of the S6 blast radius (`.github/**`, `tests/**`) and is routed to
`MIG-S7`/`MIG-S8`. It does not falsify the S6 gate — the deterministic checks all pass
today and the deploy surface is currently clean — but it is the correct thing for the next
session to close.

## Disposition

No failure to route through the Failure Arbiter. The done condition holds; deferred items
(vLLM-Omni GPU build, T-1 CI gate, X-1 WebUI/API auth-header mismatch) are honestly marked
and out of blast radius, recorded in the handoff, risk register, and eval seeds.
