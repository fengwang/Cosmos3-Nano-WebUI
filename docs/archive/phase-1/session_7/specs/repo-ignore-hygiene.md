# Specification - Repository Ignore Hygiene

Session: MIG-S7
Capability: repo-ignore-hygiene

## MODIFIED Requirements

### Requirement: Root .gitignore excludes build and environment artifacts

The root `.gitignore` MUST exclude the common Python, Node, and tooling artifacts that
contributors could otherwise commit, and the local `models/` and media artifacts (`INV-2`),
while continuing to ignore the pre-existing local-only files. This modifies the prior
`.gitignore`, which ignored only `references/`, `AGENTS.md`, `CLAUDE.md`, `ENVIRONMENTS.md`,
`REVIEW.md`, and `docs/agent_workflow/`.

Full updated behavior: the `.gitignore` SHALL ignore at least — Python
(`__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`, `.pytest_cache/`, `.ruff_cache/`,
`.benchmarks/`), Node/Next (`node_modules/`, `.next/`, `*.tsbuildinfo`), build output
(`dist/`, `build/`), model weights and media (`models/`, `*.safetensors`, `*.pt`, `*.pth`,
`*.ckpt`, `*.mp4`, `*.webm`, `*.gif` — excluding the tracked `misc/logo.png` by scope),
and the pre-existing local-only entries — and SHALL NOT newly ignore any path that is
currently tracked by Git.

#### Scenario: Common artifacts are ignored

WHEN `git check-ignore __pycache__/x.pyc .venv/ node_modules/ webui/.next/ models/w.safetensors`
runs
THEN each listed path SHALL be reported as ignored.

#### Scenario: No currently-tracked file becomes ignored

WHEN, after editing `.gitignore`, `git ls-files` is piped through `git check-ignore --stdin`
THEN no currently-tracked path SHALL be reported as ignored (the command SHALL find no
tracked file that the new patterns would exclude).

#### Scenario: Pre-existing local-only ignores are retained

WHEN the updated `.gitignore` is read
THEN it SHALL still ignore `references/`, `AGENTS.md`, `CLAUDE.md`, `ENVIRONMENTS.md`,
`REVIEW.md`, and `docs/agent_workflow/`.

#### Scenario: Working tree stays clean after the edit

WHEN `git status --short` runs after the `.gitignore` change and staging it
THEN it SHALL show only the intended edits (no previously-tracked file removed, no new
untracked artifact surfaced by the change).
