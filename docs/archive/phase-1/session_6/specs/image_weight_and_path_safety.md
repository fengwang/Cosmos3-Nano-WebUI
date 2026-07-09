# Specification - Image Weight and Path Safety

Session: MIG-S6
Capability: Image Weight and Path Safety

## ADDED Requirements

### Requirement: No weights or media are baked into images

No Dockerfile MAY `COPY` or `ADD` a model-weight or generated-media file into an
image (INV-2, R-06). A `.dockerignore` MUST exclude the checkpoint mount directory
(`models/`) and all weight/media globs so a broad copy cannot bake weights, and each
Dockerfile MUST copy only the specific source trees it needs.

#### Scenario: Weight-copy scan is clean

WHEN `rg -n "COPY .*\.(safetensors|pt|pth|ckpt)|ADD .*\.(safetensors|pt|pth|ckpt)" deploy`
runs
THEN it SHALL return no match.

#### Scenario: Build context excludes weights and bulk

WHEN `.dockerignore` is read
THEN it SHALL exclude at least `models/`, `.git`, `.venv`, `node_modules`, `.next`,
`__pycache__`, `docs`, `references`, and `*.safetensors`/`*.pt`/`*.pth`/`*.ckpt` and
common media globs.

#### Scenario: Dockerfiles copy narrow source trees

WHEN the Dockerfiles are read
THEN the `api` build SHALL copy only what it needs (e.g. `api/`, `schemas/`,
`pyproject.toml`, `uv.lock`) and the `webui` build SHALL copy only `webui/` — none
SHALL `COPY . .` of the repository root.

### Requirement: No private paths, hosts, or secrets in deployment assets

The deployment assets MUST contain no private absolute path, private host, private
codename, secret, or token (INV-1). This holds for `deploy/**`, `.dockerignore`,
`.env.example`, the `Makefile`, and `docs/session_6/**`.

#### Scenario: Private-reference scans pass

WHEN the committed private-reference scan (`tests/test_private_ref_scan.py`) and
`rg -n "$PRIVATE_REF_PATTERN" deploy docs .env.example` run over the deployment surface
THEN they SHALL return no finding (with `$PRIVATE_REF_PATTERN` treated per the S1
baseline when unset).

#### Scenario: Compose defaults use placeholders, not private paths

WHEN the FP8 and NVFP4 stacks are rendered
THEN all default host paths SHALL be repo-relative placeholders (`./models/<Repo>`)
or documented non-private examples, never a user-home or private absolute path.
