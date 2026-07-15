# Capability: vllm-omni-serve-entrypoint

Source: `docs/session_1/proposal.md` (Modified Capabilities)

## MODIFIED Requirements

### Requirement: Correct OpenAI-Compatible Serve Entrypoint
The image built from `deploy/vllm-omni.Dockerfile` MUST start the fork's
real OpenAI-compatible server via
`vllm serve <checkpoint-dir> --omni --host 0.0.0.0 --port 8000`, not the
previously guessed `python3 -m vllm_omni.entrypoints.openai.api_server`
module invocation.

#### Scenario: Container starts and becomes ready
WHEN `docker compose -f deploy/docker-compose.fp8.yml up -d vllm-omni` is
run
THEN the container remains running (does not crash-loop)
AND `curl -sf http://localhost:8000/v1/models` returns HTTP 200 within the
configured `--init-timeout`.

### Requirement: T2I Generation on FP8
The served image MUST generate a valid text-to-image artifact when queried
against the FP8 checkpoint (`wfen/Cosmos3-Nano-FP8-Blockwise`, current
pre-`GPU-S2` revision, local index-removal workaround already applied on
disk).

#### Scenario: FP8 T2I request succeeds
WHEN a T2I generation request is sent to the vLLM-Omni server serving the
FP8 checkpoint
THEN the response contains a valid image artifact
AND the request, response, and artifact metadata are recorded as evidence
in `docs/session_1/`.

### Requirement: T2I Generation on NVFP4
The served image MUST generate a valid text-to-image artifact when queried
against the NVFP4 checkpoint (`wfen/Cosmos3-Nano-NVFP4-Blockwise`, current
pre-`GPU-S2` revision, local index-removal workaround already applied on
disk).

#### Scenario: NVFP4 T2I request succeeds
WHEN a T2I generation request is sent to the vLLM-Omni server serving the
NVFP4 checkpoint
THEN the response contains a valid image artifact
AND the request, response, and artifact metadata are recorded as evidence
in `docs/session_1/`.

### Requirement: Guardrails-On Default
The image's default `CMD` MUST NOT disable content guardrails. Any
guardrails-off invocation is an explicit runtime override, never the
shipped default.

#### Scenario: Default CMD does not include --no-guardrails
WHEN `deploy/vllm-omni.Dockerfile`'s `CMD` is inspected
THEN it does not contain `--no-guardrails`.

#### Scenario: A guardrails-off override is documented, not silent
WHEN this session's T2I evidence is recorded and `--no-guardrails` was used
to obtain it
THEN the record labels that flag as a known limitation tied to the missing
gated `nvidia/Cosmos-1.0-Guardrail` model and `HF_TOKEN`, not as the image's
shipped behavior.
