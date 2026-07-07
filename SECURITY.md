# Security Policy

Cosmos3-Nano-WebUI is a **beta / research preview**. It is not hardened for
untrusted, multi-tenant, or internet-facing deployment. Please treat it
accordingly and read the deployment notes below before exposing it beyond a
trusted local network.

## Reporting a vulnerability

**Please do not open a public GitHub issue for a security vulnerability.**
Public issues are visible to everyone and can expose users before a fix exists.

Instead, report privately through one of these channels:

1. **GitHub private vulnerability reporting (preferred).** Go to the repository's
   **Security** tab → **Report a vulnerability**. This opens a private advisory
   visible only to the maintainers.
2. **Email.** If you cannot use GitHub advisories, email `feng.wang1@hexagon.com`
   with a clear description and the details below.

When you report, please include:

- a description of the issue and its impact,
- the steps or a minimal proof of concept needed to reproduce it,
- the affected component (API, WebUI, deploy config) and version/commit,
- your environment (OS, GPU/driver, Docker version) — **do not send secrets,
  API keys, tokens, or private file paths**; redact them from any logs.

We will acknowledge your report on a best-effort basis (this is a beta project
maintained without a formal SLA) and coordinate a fix and disclosure timeline
with you before any public write-up.

## Scope

In scope: source code in this repository (the API and WebUI, deploy/Compose
config).

Out of scope (report upstream to the respective project):

- the Hugging Face model weights and model cards (`wfen/Cosmos3-Nano-*`,
  `nvidia/Cosmos3-Nano`),
- the pinned `vllm-omni` fork and other third-party dependencies.

## Deployment notes that affect security

- **Authentication is off by default.** Set `COSMOS3_API_KEY` to require an
  `X-API-Key` on the job/artifact routes. Enable it (and network controls)
  before exposing the API beyond a trusted local network.
- **Loopback by default.** The Compose stacks publish ports on `127.0.0.1`
  (`BIND_ADDR`); change this deliberately.
- **Docker socket privilege.** The API container mounts the host Docker socket
  to drive the generation container (root-equivalent on the host). Access is
  confined to a fixed-verb controller, but do not expose this container to
  untrusted callers. See `docs/risk_register.md` (R-16).

Thank you for helping keep the project and its users safe.
