"""Async job model (S6) — the INV-5 contract.

Immutable `JobRecord` + pure lifecycle transitions (`model`), a per-job bounded SSE event log
with `Last-Event-ID` replay (`events`), an in-memory store + idempotency registry (`store`),
a single serialized async runner that acquires the orchestrator slot (`runner`), and local
artifact I/O (`artifacts`). Refs: session_6/specs/async-job-model.md.
"""
