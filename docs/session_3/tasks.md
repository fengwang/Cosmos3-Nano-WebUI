# Session 3 Tasks - Joint Validation on RTX 5090

## 1. Setup

- [x] 1.1 Create `GPU-S3` branch off `GPU-S2`
- [x] 1.2 Scaffold `docs/session_3/{probes,specs}/`
- [x] 1.3 Write the planning pack (brainstorming, proposal, design, specs,
      tasks, plan, execution contract)

## 2. Probe library (shared pure code)

- [ ] 2.1 Write `docs/session_3/probes/lib.py`: `Verdict` enum,
      `EvidenceRecord` frozen dataclass, pure checkers
      (`check_no_lfs_pointers`, `check_valid_image`, `check_job_terminal`,
      `check_image_freshness`), pure `build_evidence_record`.
- [ ] 2.2 Write `docs/session_3/probes/test_lib.py` covering each pure
      checker against both a passing and a failing synthetic input — no
      GPU, no network required to run this.

## 3. T1 - Fresh checkpoint fetch

- [ ] 3.1 Write `docs/session_3/probes/run_checkpoint_fetch.py`
      (`--checkpoint {fp8,nvfp4}`).
- [ ] 3.2 Run it for FP8: fresh `hf download` into
      `models/Cosmos3-Nano-FP8-Blockwise`; verify no LFS pointers / stale
      index; write `evidence_checkpoint_fetch_fp8.json`.
- [ ] 3.3 Run it for NVFP4: same, into `models/Cosmos3-Nano-NVFP4-Blockwise`;
      write `evidence_checkpoint_fetch_nvfp4.json`.

## 4. T2 - GPU-S1 image freshness

- [ ] 4.1 Compare `deploy/vllm-omni.Dockerfile` mtime against
      `cosmos3-nano-vllm-omni:local`'s `Created` timestamp
      (`docker image inspect`).
- [ ] 4.2 If stale, `docker compose -f deploy/docker-compose.fp8.yml build
      vllm-omni`; if current, proceed without rebuilding.

## 5. T3/T4 - Direct vLLM-Omni T2I

- [ ] 5.1 Write `docs/session_3/probes/run_direct_t2i.py`
      (`--checkpoint {fp8,nvfp4}`).
- [ ] 5.2 Run for FP8: `make up-fp8`, direct request to the vLLM-Omni
      container, validate artifact, `make down`; write
      `evidence_direct_t2i_fp8.json`.
- [ ] 5.3 Run for NVFP4: same via `make up-nvfp4`; write
      `evidence_direct_t2i_nvfp4.json`.

## 6. T5/T6 - Full-stack T2I through the api

- [ ] 6.1 Write `docs/session_3/probes/run_fullstack_t2i.py`
      (`--checkpoint {fp8,nvfp4}`).
- [ ] 6.2 Run for FP8: `X-API-Key` -> `POST /v1/generation/t2i` -> poll job
      -> `GET` artifact; write `evidence_fullstack_t2i_fp8.json`.
- [ ] 6.3 Run for NVFP4: same; write `evidence_fullstack_t2i_nvfp4.json`.

## 7. T7 - Best-effort T2V smoke

- [ ] 7.1 Write `docs/session_3/probes/run_t2v_smoke.py`.
- [ ] 7.2 Attempt NVFP4 first at 256px, minimal frames, direct-only; on
      `FAIL`/OOM, attempt FP8 once; write `evidence_t2v_smoke.json`
      regardless of outcome (`PASS`/`FAIL`/`SCOPED_OUT`).

## 8. T8 - Evidence aggregation and doc sync

- [ ] 8.1 Write `docs/session_3/probes/aggregate.py`; run it to produce
      `probes/evidence.json` + `probes/summary.md`.
- [ ] 8.2 Update `docs/evidence_map.md` with the new GPU-S3 evidence rows.
- [ ] 8.3 Update `docs/eval_seed_cases.md`: close `EV-GPU-FP8-T2I`,
      `EV-GPU-NVFP4-T2I`, `EV-GPU-T2V-SMOKE`, `EV-GPU-JOBS-ARTIFACT`.
- [ ] 8.4 Update `docs/model_setup.md` §6/§8 per-mode markings.
- [ ] 8.5 Update `docs/release_checklist.md` §7 per-mode markings.
- [ ] 8.6 Update `README.md` per-mode markings.
- [ ] 8.7 Update `docs/risk_register.md`: close R-05 and R-09 (`GPU-S3`), or
      add a new row if a new failure form surfaces.

## 9. Review and verification

- [ ] 9.1 Sharded review across correctness, security, tests, architecture,
      performance.
- [ ] 9.2 Fix High/Critical findings only; re-run targeted checks.
- [ ] 9.3 Adversarial verification (fresh context, tries to falsify the done
      condition).
- [ ] 9.4 Failure Arbiter classification for any check that fails twice the
      same way.

## 10. Session close

- [ ] 10.1 Write `docs/handoff.md` from the template.
- [ ] 10.2 Harvest eval seeds to `docs/eval_corpus/` for anything caught or
      missed this session.
- [ ] 10.3 Final commit(s).
