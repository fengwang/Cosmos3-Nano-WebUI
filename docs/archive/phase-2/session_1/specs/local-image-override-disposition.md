# Capability: local-image-override-disposition

Source: `docs/session_1/proposal.md` (Removed Capabilities)

## REMOVED Requirements

### Requirement: Local-Image Compose Override

FROM: `deploy/docker-compose.local-image.yml` existed (untracked) as an
undispositioned stopgap that pointed the `vllm-omni` service at a prebuilt
local image (`vllm-omni-local:c89089a4`) and the fork's real
`vllm serve … --omni` command, bypassing `deploy/vllm-omni.Dockerfile`
entirely.

**Reason:** PRD Owner Decision 8 requires `GPU-S1` to disposition this
stopgap rather than leave it as a de facto serving path. Now that
`deploy/vllm-omni.Dockerfile` itself builds and serves T2I successfully
(this session's other two capabilities), the stopgap's purpose is gone. The
owner chose removal over keeping it as a documented "reuse a prebuilt
image" convenience.

**Migration:** None required — the file was never committed, so no
existing clone or checkout references it. An operator who still wants to
reuse a prebuilt image writes their own Compose override following the
`include:` pattern already used by `deploy/docker-compose.fp8.yml` and
`deploy/docker-compose.nvfp4.yml` over `deploy/docker-compose.base.yml`.

#### Scenario: File is absent after this session
WHEN the repository tree is inspected after this session closes
THEN `deploy/docker-compose.local-image.yml` does not exist
AND `git status` shows it neither tracked nor untracked.
