"""vllm-omni generation engine (out-of-process, container-served; torch-free).

`client` is the async video-API HTTP client (submit/poll/download over an injected
transport); `work` is the `Work`-shaped adapter the runner injects as `job_work`.
Kept import-light (no torch at import) so the torch-free server/host loop can import
it. Refs: session_4/specs/vllm-omni-video-client.md, vllm-omni-generation-adapter.md.
"""
