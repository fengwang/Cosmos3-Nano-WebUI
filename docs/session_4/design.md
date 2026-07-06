# Session 4 Design - Hugging Face Checkpoint Verification and Model Setup Docs

Date: 2026-07-06
Session: MIG-S4
Status: Derived from approved brainstorming + proposal

## Context

The public beta serves external weights from `wfen/Cosmos3-Nano-FP8-Blockwise` and
`wfen/Cosmos3-Nano-NVFP4-Blockwise`. Session 3 imported loaders whose checkpoint
expectations are concrete and testable:

- `api/engines/diffusers_oracle/loader.py:discover_transformer_dir` requires a
  transformer directory containing `*.safetensors` + `modelopt_state.pt` +
  `config.json` (tries nested `transformer/transformer/`, then flat `transformer/`).
- Precision is read from `<root>/quantization_config.json` (`recipe`, `scale_layout.granularity`)
  and confirmed by observing `weight_quantizer._double_scale` (NVFP4) vs its absence (FP8).
- `api/engines/vllm/reasoner_preflight.py` scans `transformer/*.safetensors` headers to
  keep the understanding tower BF16 (blockwise-quant sidecar suffixes flagged).
- The action/forward_dynamics graft (`api/engines/diffusers_action`) and the reasoner
  (`api/engines/vllm`) both read a **BF16 base model** (`COSMOS3_BASE_ACTION_DIR`,
  `COSMOS3_REASONER_MODEL_DIR`).

Both the HF network and the local checkpoints (under the `/data/models/<Repo>` mount
convention) are reachable from the build host, so verification is executable.

Constraints: docs-only blast radius (no code/schema/Docker/README/`.github`); HIGH
risk / branch_and_compare; provenance guardrail R-01 dominates (no dev-only variant
names, no host paths). Stakeholders: S6 (Docker), S7 (README), S8 (release gate)
consume the outputs.

## Goals / Non-Goals

**Goals**
- Record both public HF revisions and the model license, reproducibly.
- Capture the full public file manifest (sizes + LFS SHAs) and model-card state.
- Verify public layout + quantization metadata against loader expectations, using
  local header probes cross-checked to the public artifact via LFS SHA.
- Produce an authoritative `docs/model_setup.md` contract with a per-mode
  compatibility matrix.
- Disposition every drift and route it before Docker/README depend on it.

**Non-Goals**
- No torch/diffusers/GPU load (that is the `MIG-S8` gate).
- No code, schema, Docker, README, or `.github` edits.
- No HF write (model-card fixes are recommended as follow-ups, not performed).
- No download of large blobs in CI (header-only partial reads on already-present
  local files; network calls are metadata-only).

## Decisions

**D1 — Executable probe as the single evidence source (Approach A).**
A torch-free probe under `docs/session_4/probes/` gathers all machine facts and emits
`evidence.json` + `summary.md`. Rationale: reproducible, strongest for a HIGH gate,
centralizes provenance scrubbing. Alternative (ad-hoc transcription) rejected as
non-reproducible and leak-prone; alternative (real torch load) rejected as out of scope.

**D2 — HF metadata is authoritative; local probes are supplemental and gated by SHA.**
`HfApi.list_repo_files` + `get_paths_info` give the *public* file set with sizes and
LFS SHAs. Local safetensors headers are parsed only from files whose local blob SHA
equals the public LFS SHA (`local == public`), so header findings describe the public
artifact. Rationale: the local mount may hold a different build; the SHA gate makes
local evidence trustworthy without downloading multi-GB blobs. Alternative (range-GET
headers from HF) rejected as more complex with no added trust over the SHA gate.

**D3 — 404 for the base repo is expected Data, not an error (define-errors-away).**
Reachability is a value (`REACHABLE` / `NOT_FOUND` / `ERROR`), so the non-public base
model is a finding that drives the beta-limited matrix, not an exception. Rationale:
the gap is the point of the session; modelling it as data keeps the probe from
crashing on the expected case.

**D4 — Reuse `tools/checkpoint_prep/safetensors_io.py:parse_header`.**
It is pure, torch-free, and already tested; the probe reads only the leading
`8 + N` header bytes of each `*.safetensors` (partial read, no full-tensor load).
Rationale: no new parser, no new dependency, consistent with the runtime's own format
handling.

**D5 — Provenance scrub is a pure calculation at the reporting boundary.**
Every value written to a doc passes through `scrub(...)`: public repo IDs + revisions
pass; the local mount root is rendered as `/data/models/<Repo>` or `/path/to/<Repo>`;
dev-only variant names and host paths are rejected/replaced. Rationale: R-01 and the
S3 eval seed — the leak recurred in planning docs, so scrubbing is enforced in code,
plus a private-value regression over `docs/session_4/**` before each commit.

**D6 — Per-mode compatibility matrix drives the contract.**
Generation modes (t2v, t2i, i2v, t2v_audio) are backed by the two public checkpoints;
reasoning and action/forward_dynamics require the non-public BF16 base and are marked
beta-limited. Rationale: INV-8 / R-08 — ship with clearly-marked unverified surfaces
rather than blocking or overclaiming.

## Probe Architecture — ACD Blueprint

The probe is an **impure shell** (network + filesystem + file write) orchestrating a
**pure core** (parse / derive / compare / diff / scrub / render).

### Step 1 — ACD classification

| Requirement | ACD Class | Reasoning |
|---|---|---|
| Resolve revision (`git ls-remote` / `HfApi.model_info().sha`) | Action | network state |
| Fetch license + `card_data` + card file size | Action | network |
| List repo files + `get_paths_info` (size, LFS sha) | Action | network |
| Read local `*.safetensors` header bytes (partial) | Action | filesystem |
| Read local `config.json` / `quantization_config.json` | Action | filesystem |
| `parse_header(raw)` → header dict | Calculation | pure (reused) |
| `precision_from_quant_config(cfg)` → (Precision, granularity) | Calculation | pure map |
| `precision_from_header_keys(header)` → Precision | Calculation | pure over keys |
| `crosscheck(local_manifest, public_manifest)` → results | Calculation | pure comparison |
| `evaluate_layout(manifest, expectations)` → findings | Calculation | pure predicates |
| `derive_drift(findings, crosschecks, cards, reach)` → drifts | Calculation | pure |
| `scrub(value, rules)` → public string | Calculation | pure string map |
| `build_bundle(...)` → EvidenceBundle | Calculation | pure construction |
| `render_summary(bundle)` → markdown | Calculation | pure |
| `evaluate_assertions(bundle, expected)` → results | Calculation | pure (spec scenarios) |
| Write `evidence.json` + `summary.md`; print report | Action | filesystem write / stdout |

### Step 2 — Deep public interface + pure core

Facade (the only Action entry point; all inputs explicit, no globals):

```
# Probe both public repos + the base-repo reachability check against the local
# mount root, cross-checking local files to public LFS SHAs. Pure core; the only
# side effects are the two output files under `out_dir`. Network/FS failures on a
# required repo raise ProbeError (documented); a 404 base repo is REACHABILITY data.
function run_probe(config: ProbeConfig) -> EvidenceBundle
```

`ProbeConfig` (immutable boundary Data): `repos: list[RepoSpec]`, `base_repo: RepoId`,
`mount_root: Path`, `out_dir: Path`. Pure core functions listed in the ACD table are
individually testable without network or disk.

### Step 3 — Data flow

```
ProbeConfig
  [Action: resolve_revision(repo)]        → Revision
  [Action: fetch_card(repo)]              → LicenseId, CardState
  [Action: list_public(repo)]             → Manifest(public)   (path,size,lfs_sha)
  [Action: read_local_headers(mount)]     → Manifest(local) + {path: Header}
    → crosscheck(local, public)           → list[CrossCheck]           (Calc)
    → precision_from_quant_config(cfg)    → Precision, granularity     (Calc)
    → precision_from_header_keys(header)  → Precision                  (Calc)
    → evaluate_layout(public, EXPECTATIONS)→ list[LayoutFinding]        (Calc)
    → derive_drift(...)                   → list[Drift]                (Calc)
    → build_bundle(scrub∘all)             → EvidenceBundle             (Calc)
  [Action: write_json + write_summary]    → files
    → evaluate_assertions(bundle, EXPECTED)→ AssertionReport           (Calc)
  [Action: print report / nonzero exit on fail]
```

### Step 4 — Data types (no boolean/null blindness)

- `enum Precision { FP8, NVFP4, UNKNOWN }`
- `enum CardState { POPULATED, EMPTY, ABSENT }`
- `enum Reachability { REACHABLE, NOT_FOUND, ERROR }`
- `enum CrossCheck { MATCH, MISMATCH, LOCAL_ABSENT, NO_LFS_SHA }`
- `FileEntry { path, size, lfs_sha | None }`, `Manifest = list[FileEntry]`
- `LayoutFinding { expectation, satisfied: SatisfyState, evidence }` where
  `SatisfyState ∈ { SATISFIED, MISSING, ALTERNATE }`
- `Drift { id, summary, severity, disposition, routed_risk }`
- `EvidenceBundle { generated_context, repos: [...], crosschecks, findings, drifts }`

### Step 4b — Error strategy (pyramid)

| Operation | Failure mode | Tier | Residual contract |
|---|---|---|---|
| `resolve_revision(base_repo)` | 404 not found | define-away | `Reachability.NOT_FOUND` data, no raise |
| `list_public(repo)` | transient network | propagate | `ProbeError` (documented) — required repo must resolve |
| `read_local_headers` | local mount absent | aggregate | per-repo `local_probe: LOCAL_ABSENT`, bundle still built |
| `parse_header(raw)` | truncated header | propagate | `ValueError` (from reused parser), documented |

Masking/retry are not used (network is reachable and CI must fail loudly on a
required-repo outage). No exception is swallowed; the base-repo 404 is data by design.

### Step 5-7 — Parallelism assessment

**No parallelism opportunity identified.** The collection is tiny (2 repos + 1
base check); per-item work is dominated by isolated network **Actions** (Check 6 does
not warn on Action bodies), and the pure header parses are a handful of small partial
reads. Serial total is well under the ~100 ms overhead threshold for worth-parallelizing
work. Keep serial; revisit only if the repo set grows.

## Risks / Trade-offs

- [Local mount is a different build than public] → SHA cross-check gates every local
  header finding; on `MISMATCH`/`NO_LFS_SHA` the finding is downgraded to
  "public-manifest-only" and noted, never asserted as verified.
- [Provenance leak into session docs (R-01, recurred in S2/S3)] → `scrub()` calculation
  + private-value regression over `docs/session_4/**` before every commit; probe
  output is scrubbed before embedding.
- [NVFP4 metadata asymmetry blocks a target mode] → characterize precisely; if the
  loader path still resolves (observe-precision fallback), document it; if not, raise a
  drift with a routed risk row and mark the mode beta-limited (do not fix code here).
- [`huggingface_hub` API drift across versions] → pin usage to stable calls
  (`model_info`, `list_repo_files`, `get_paths_info`); on `ImportError`/`AttributeError`
  classify ENVIRONMENT and fall back to `git ls-remote` + documented browser evidence
  (per session_4.md).
- [Non-public base model surprises downstream] → explicit beta-limited matrix in
  `model_setup.md` + risk row so S6/S7/S8 inherit the constraint.

## Migration Plan

1. Land the refining pack (specs, tasks, plan, execution_contract).
2. Build the probe with spec-derived assertions (TDD: pure-core unit checks first).
3. Run the probe; capture `evidence.json` + `summary.md`.
4. Author `hf_verification.md`, `model_setup.md`, `drift_report.md` from the bundle.
5. Update `evidence_map.md`, `risk_register.md`, `eval_seed_cases.md` + `eval_corpus/`.
6. Full checks + private-value regression → sharded review → fix High/Critical →
   adversarial verifier → handoff.

Rollback: this session is additive documentation on `session-4`; reverting the branch
removes all artifacts with no runtime impact.

## Open Questions

- None blocking. Optional follow-ups (out of scope, recommended in the drift report):
  populate the NVFP4 model card and remove dev-scratch files from the public FP8 repo
  (HF-side writes); decide whether to publish a BF16 base repo to back reasoning/action.
