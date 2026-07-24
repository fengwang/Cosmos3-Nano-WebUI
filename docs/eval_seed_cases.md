# Eval Seed Cases - Single-GPU Comfort and ADHD-Friendly Onboarding

Date: 2026-07-24

These cases seed the deterministic checks for `LX-S1` and `LX-S2`. All blocking
checks this phase are **deterministic and host-runnable**; **no GPU smoke is
required or blocking** (PRD Decision 9). GPU inference remains the standing
`MIG-S8` manual gate, unchanged by this phase.

## Fixed references (unchanged this phase)

- Public checkpoints and the vLLM-Omni pin are unchanged; see
  `docs/model_setup.md` and `.env.example` for the pinned revisions. This phase
  changes no checkpoint revision, no pin, and no network/auth posture.
- Timeouts audited but **not** changed: `COSMOS3_GEN_TIMEOUT` (2400 s / 7200 s,
  E-03), `COSMOS3_PLANE_READY_TIMEOUT` (1800 s, E-04), `COSMOS3_REASONER_TIMEOUT`
  (300 s), WebUI SSE `heartbeatTimeoutMs` (30 s, E-08).

## Deterministic Checks (blocking)

| ID | Purpose | Inputs | Expected properties | Gate |
|---|---|---|---|---|
| EV-LX-IDLE-DEFAULT-1800 | The shipped idle keep-warm default is 30 min, at both sources of truth, and stays overridable. | A CPU unit test that builds the app with no timeout env set and reads the wired idle timeout; a test with `COSMOS3_IDLE_TIMEOUT_SECONDS` set to another value; a test with it set to `0`. Plus `rg -n "COSMOS3_IDLE_TIMEOUT_SECONDS" api/app/main.py` and `rg -n "idle_timeout" api/orchestrator/manager.py`. | App-wired idle timeout == 1800.0 with no env; an explicit override is honored; `0` disables eviction (no timer scheduled); both the `main.py` fallback and the `Orchestrator` constructor default read 1800. | LX-S1 |
| EV-LX-TIMEOUT-AUDIT | Confirm the change targets the right knob: generation and cold-start ceilings already cover ≥30-min work. | Inspection recorded in `docs/evidence_map.md` (E-03/E-04): `api/jobs/gen_client.py:129`, `api/engines/vllm_omni/work.py:41,128`, `api/app/main.py:177`, `deploy/vllm-omni.Dockerfile:41`. | The recorded audit shows `COSMOS3_GEN_TIMEOUT` ≥ 2400 s and `COSMOS3_PLANE_READY_TIMEOUT` = 1800 s, and no other timeout is changed by the session. | LX-S1 |
| EV-LX-ENV-EXAMPLE-DOC | The idle knob is surfaced consistently for discoverability. | `rg -n "COSMOS3_IDLE_TIMEOUT_SECONDS" .env.example`. | One commented entry describing the idle keep-warm window in seconds; the documented default matches the code default (1800); `0` = never evict noted. | LX-S1 |
| EV-LX-CPU-SUITE-GREEN | The CPU suite stays green after the timeout change. | `uv run pytest -m "not gpu"`. | All green, including the new idle-default test; no other test perturbed (the change is a single default value). | LX-S1 |
| EV-LX-README-RUNNABLE-QUICKSTART | The rewritten README still contains a runnable fastest-path. | Spec-derived asserts over `README.md`: the TL;DR/quickstart contains clone → a pinned public `hf download` → `make build` → `make up-fp8` → `make health` → open the Studio; cross-check each `make` target exists in `Makefile`. | Every essential step present and in order; every referenced `make` target resolves in the `Makefile`; commands are in fenced blocks with a language identifier. | LX-S2 |
| EV-LX-README-HONEST-CAVEATS | The full honest caveats survive, visible, at the end. | Grep/structure asserts over `README.md`: a "Status & security" (or equivalent) section exists, is **not** wrapped in `<details>`, and appears in the final third of the document; it contains the five posture facts (no app auth; loopback default / LAN opt-in; root-equivalent Docker socket; guardrails-off; per-mode verification) and the new 30-min idle behavior. | All five posture facts present in visible prose; the section is not inside a collapsible; the 30-min keep-warm behavior is stated. | LX-S2 |
| EV-LX-README-VERIFIED-SUBSET | No mode is claimed verified beyond the evidence. | Compare every "GPU-verified" / "verified end to end" claim in `README.md` against the evidence-map verified set (text→image only, E-20). | Only text→image is called GPU-verified end to end; every other mode is "implemented · CPU-tested · GPU gate (`MIG-S8`)"; no hook/benefit line implies otherwise. | LX-S2 |
| EV-LX-README-STRUCTURE | The ADHD structural techniques are present (properties, not prose). | Structure asserts over `README.md`: a hook precedes deep install; a TL;DR block near the top; at least one ` ```mermaid ` fenced block (≤7 nodes); at least one `<details>`/`<summary>` for verbose content; in-page anchors / a TOC. | Each property present; the Mermaid block parses and has ≤7 nodes; each `<details>` has a blank line after `</summary>`. | LX-S2 |
| EV-LX-DOCS-LINKS-RESOLVE | Every internal link resolves and there is no cloud CTA. | Relative-link + in-page-anchor resolver over `README.md` (and any doc it links that the session edits); `rg -in "codespace\|devcontainer\|open in cloud\|launch in the cloud" README.md`. | Every relative link and anchor points at an existing target; zero Codespaces/cloud call-to-action matches. | LX-S2 |

## Manual GPU Smokes

**None this phase.** Both sessions are fully verifiable with the deterministic,
host-run checks above: `LX-S1` idle eviction is exercised through the
orchestrator's injected timer without a GPU, and `LX-S2` is documentation.
A GPU smoke is neither required nor a blocking gate (PRD Decision 9 / NFR-4).

## Evidence Fields

Not applicable this phase (no GPU smoke). If a future session promotes any of
the audited timeouts to a measured change, record the standard fields
(hardware, driver/CUDA, checkpoint repo + revision, request shape, peak VRAM,
guardrails posture, artifact metadata, result) per the archived
`docs/archive/phase-3/eval_seed_cases.md` template.
