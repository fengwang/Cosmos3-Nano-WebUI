# Session 4 Adversarial Verification

Date: 2026-07-06
Session: MIG-S4
Method: fresh-context, read-only verifier per `docs/agent_workflow/prompts/adversarial_verifier.md`.
It did not see the implementation conversation; it saw only the session contract, project
contract, the diff (`4b868d1..HEAD`), and the evidence, and was tasked to FALSIFY
"GATE-MIG-S4-HF passes with public checkpoint setup ready for Docker and README."

## Verdict: PASS (with one LOW process finding, resolved)

The verifier could not falsify the done condition. It independently reproduced every
load-bearing fact.

## Independently verified

- **Revisions (deterministic):** FP8 `4e181f99…`, NVFP4 `b5c9332e…`, base `fea6e03a…` all
  match `evidence.json`/`hf_verification.md`/`model_setup.md`; `wfen/Cosmos3-Nano` → 404 (D2).
- **D1 is real and non-tautological:** `config.py:45` requires exact `recipe == "fp8"`; the
  public FP8 recipe `fp8_blockwise_mixed` hits `raise ValueError` (`config.py:47`).
  `discover_transformer_dir` (`loader.py:41-49`) requires `modelopt_state.pt`; NVFP4 lacks it →
  `FileNotFoundError`. `build_oracle` (`loader.py:160-162`) calls discovery before verify. The
  probe `--check` pins the exact-`"fp8"` semantic (a `startswith` regression fails it).
- **Default engine `vllm_omni`** (`app/main.py:103`) — D1 scoping to the in-process path is accurate.
- **Base public/ungated (D2/FA-1):** `nvidia/Cosmos3-Nano` `gated=False, private=False`, has
  `transformer/` + `vision_encoder/`; specs correctly encode "publicly backed", not
  "beta-limited (non-public base)".
- **Env-table `file:line` citations** all match the code; the internal default inconsistency is real.
- **SHA gate is real** (a local mount is present): the fresh full-probe run reproduced
  `crosscheck: match` / `verified_for_public: true` and identical drift IDs; exit 0.
- **INV-1/2/4/7 hold:** no weights/secrets/private hosts in the diff; the only dev-variant /
  blockwise-suffix detector hits are the rg pattern definitions in `plan.md`/`execution_contract.md`;
  licenses kept separate from repo MIT.

## LOW finding (change-control) — resolved

- **Finding:** `git diff --name-only 4b868d1..HEAD` includes two files outside the contract's
  `blast_radius.allowed_files`: `docs/eval_corpus/mig_s4_base_model_publication_premise.md` and
  `docs/eval_corpus/mig_s4_nvfp4_loader_layout_drift.md`. The contract listed `docs/session_4/**`,
  `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/model_setup.md`
  — but not `docs/eval_corpus/**`.
- **Why it is LOW / not a done-condition falsification:** the Session End Protocol step 4
  mandates "Add eval seeds to `docs/eval_corpus/`"; the session's own `plan.md`/`execution_contract.md`
  planned exactly these files; `docs/eval_corpus/` is an established convention (S2/S3 seeds live
  there and are referenced by `eval_seed_cases.md`); and both files passed the INV-1 scan. The
  contract's `allowed_files` simply omitted the protocol-mandated `docs/eval_corpus/**`.
- **Resolution:** classified SPEC_GAP (Failure Arbiter FA-4); `session_4_contract.yaml`
  `blast_radius.allowed_files` amended to add `docs/eval_corpus/**` and `docs/handoff.md` (the same
  Session-End-Protocol omission; S1–S3 also wrote `docs/handoff.md`), reconciling the contract with
  the Session End Protocol and the S2/S3 convention. Recorded in `failure_arbiter.md` FA-4 and the
  handoff. No secret/weight/forbidden-surface file was involved.

## Disproven claims: none. Unsupported claims: none material.
