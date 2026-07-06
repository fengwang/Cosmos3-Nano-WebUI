# Session 4 Plan - Hugging Face Checkpoint Verification and Model Setup Docs

Session: MIG-S4
Input: `tasks.md` (what), `design.md` (how), `specs/*.md` (scenarios → assertions)

Verification environment: host `python3` with `huggingface_hub` 1.21.0 (probing tool
only; the runtime's 3.12 pin is not required for torch-free metadata/header probes).
All commands run from the repo root `/workspace/github.repo/Cosmos3-Nano-WebUI`.

## Task 1 — Verification probe (TDD)

**1.1 Pure core + `--check` first (red → green).**
File: `docs/session_4/probes/verify_hf_checkpoints.py`.

Write the calculations and their assertions before the network shell. The reused
parser is imported without adding a dependency:

```python
# make tools/checkpoint_prep importable without installing the package
_TOOLS = pathlib.Path(__file__).resolve().parents[3] / "tools"
sys.path.insert(0, str(_TOOLS))
from checkpoint_prep.safetensors_io import parse_header  # pure, torch-free
```

Pure functions (no I/O): `precision_from_quant_config(cfg) -> (Precision, str)`,
`precision_from_header_keys(header) -> Precision`, `crosscheck(local, public) ->
list[CrossCheck]`, `evaluate_layout(manifest, EXPECTATIONS) -> list[LayoutFinding]`,
`derive_drift(...) -> list[Drift]`, `scrub(value, rules) -> str`, `build_bundle(...)`,
`render_summary(bundle) -> str`.

Spec-derived self-test (`--check`) asserts the pure functions against fixture inputs,
e.g.:

```python
assert precision_from_header_keys({"x.weight_quantizer._double_scale": {}}) is Precision.NVFP4
assert precision_from_header_keys({"x.weight_quantizer._scale": {}}) is Precision.FP8
assert scrub("/data/models/Cosmos3-Nano-FP8-Blockwise") == "/data/models/Cosmos3-Nano-FP8-Blockwise"
assert scrub("/opt/scratch/unpublished-variant") == "<scrubbed>"  # path outside the allowed convention is rejected
```

Run (must pass before writing the shell):
```bash
python3 docs/session_4/probes/verify_hf_checkpoints.py --check
```

**1.2 Action shell.** Add the thin impure layer: `resolve_revision(repo)` (HfApi +
`git ls-remote` consistency), `fetch_card(repo)`, `list_public(repo)` (`list_repo_files`
+ `get_paths_info`), `read_local_headers(mount_root/repo)` (open file, read 8 bytes,
read N header bytes, `parse_header`), `write_json`, `write_summary`. Base-repo 404 →
`Reachability.NOT_FOUND` (no raise). CLI flags: `--fp8-repo`, `--nvfp4-repo`,
`--base-repo` (default to the public IDs), `--mount-root` (default `/data/models`
mount convention), `--out` (default `docs/session_4/probes`).

**1.3 Run + capture.**
```bash
python3 docs/session_4/probes/verify_hf_checkpoints.py --out docs/session_4/probes
python3 docs/session_4/probes/verify_hf_checkpoints.py --check   # spec assertions green
```
Outputs: `docs/session_4/probes/evidence.json`, `docs/session_4/probes/summary.md`.

**Commit point A:** `feat(s4): HF checkpoint verification probe + evidence bundle`
(after the private-value regression over `docs/session_4/**` is clean).

## Task 2–4 — Author deliverables from the bundle

- **2.1** `docs/session_4/hf_verification.md` — transcribe the scrubbed bundle into the
  verification note; cite `evidence.json` and the exact HfApi/ls-remote commands.
- **3.1** `docs/model_setup.md` — the authoritative contract (see
  `specs/public_model_setup_contract.md`).
- **4.1** `docs/session_4/drift_report.md` — D1–D4 with severity/disposition/risk row.

**Commit point B:** `docs(s4): HF verification note, model setup contract, drift report`.

## Task 5 — Evidence / risk / eval updates

- **5.1** `docs/evidence_map.md`: append rows for FP8/NVFP4 revisions, license, layout,
  self-containment, and each drift, dated to the verification date.
- **5.2** `docs/risk_register.md`: update R-03 (HF differs from runtime) and R-04
  (empty NVFP4 card) with the outcome; add rows for D1 (NVFP4 metadata) and D3
  (external hygiene) if warranted.
- **5.3** `docs/eval_seed_cases.md` + `docs/eval_corpus/mig_s4_*.md`: add
  EV-MIG-HF-FP8-METADATA, EV-MIG-HF-NVFP4-METADATA, and any caught/missed seed.

**Commit point C:** `docs(s4): evidence map, risk register, eval seeds`.

## Task 6–7 — Verify, review, close

- **6.1** Full checks:
```bash
git ls-remote https://huggingface.co/wfen/Cosmos3-Nano-FP8-Blockwise HEAD 'refs/heads/*'
git ls-remote https://huggingface.co/wfen/Cosmos3-Nano-NVFP4-Blockwise HEAD 'refs/heads/*'
python3 -c "import huggingface_hub; print(huggingface_hub.__version__)"
rg -n "wfen/Cosmos3-Nano-(FP8|NVFP4)-Blockwise" docs
python3 docs/session_4/probes/verify_hf_checkpoints.py --check
# private-value regression over this session's own docs:
rg -n -i -e '-wfen' -e 'Blockwise-dist' -e 'Blockwise-local' -e 'NVFP4-AWQ' \
   -e '/data/home' -e '/home/[a-z]' -e 'intranet' -e 'hf_[A-Za-z0-9]{20}' \
   -e 'sk-[A-Za-z0-9]{20}' docs/session_4/ docs/model_setup.md
```
Classify any failure with the Failure Arbiter before fixing.
- **6.2** Sharded review over the five axes; save `sharded_review.md`; fix only
  High/Critical; re-run 6.1.
- **6.3** Adversarial verifier (fresh context; sees only contract + diff + evidence);
  save `adversarial_verification.md`.
- **7.1** Verify `GATE-MIG-S4-HF`; write `docs/handoff.md`; add eval seeds; list
  remaining risks.

**Commit point D:** `review(s4): sharded review + adversarial verification (PASS), handoff, eval seeds`.

Do not push. Commits stay local on `session-4`.
