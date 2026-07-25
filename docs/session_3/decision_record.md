# AM-S3 Decision Record — Action enabled on FP8 (zero-BF16)

Date: 2026-07-25 · Session: AM-S3 · Risk: high · Gate: `GATE-AM-S3-ACTION`
Owner quality: ✅ **Feng — OWNER-AM-ACTION-QUALITY = PASS (2026-07-25)** · **GATE-AM-S3-ACTION PASSES**
Hardware: RTX 5090 (sm_120), 32 GiB. Evidence: `docs/session_3/evidence/P1–P2`, `brainstorming.md`,
`design.md`, `execution_contract.md`, `sharded_review.md`, `adversarial_verification.md`.

## 1. TL;DR decisions
| Question | Decision | Basis |
|---|---|---|
| How is action served zero-BF16 on FP8? | **`(a2)` — the resident vllm-omni model via the video-API `action_mode`.** FD=sync `/v1/videos/sync`; policy/ID=async `/v1/videos` (trajectory in the top-level `action`). | P1/P2 (GPU): all 3 v1 modes off the quantized-only checkpoint; ID matches the shipped expected output (mean\|Δ\|=0.015). |
| `(a1)` openpi WS vs `(a2)` video-API? | **`(a1)` NO-GO for the base checkpoint** (needs a model `policy_server_config`; it targets the separate `nvidia/Cosmos3-Nano-Policy-DROID`). **`(a2)` GO.** | Fork source @6970350 (`ServingRealtimeRobotOpenPI.create_policy_server` → None) + the Cosmos3-Nano recipe. |
| `(c)` diffusers in-process plane? | **Not built — left dormant** (R-11). | `(a2)` GPU-proven → the third `Plane.ACTION` is unnecessary; owner confirmed a2-only. |
| Checkpoint re-export? | **None** (E-06 refuted; adapters already bundled). | AM-S1 P1/P2; byte-verified again in AM-S3 P1. |
| Zero-BF16 (INV-4)? | **`COSMOS3_BASE_ACTION_DIR` retired** (no default → `None`); action rides the quantized checkpoint. | loader + `.env.example`; `docker compose config` shows no BF16 mount. |

## 2. What was asked (and answered)
AM-S3: make action run end to end on FP8 off a quantized-only checkpoint and obtain the owner's quality
PASS, without regressing `t2i`. Answered: the resident omni model serves all three v1 modes via the
video-API `action_mode` (P1/P2), zero-BF16, one resident model (Studio+Action merge); `t2i` non-regressed;
CPU green; schema unchanged. The **only** remaining item is the owner's trajectory-quality signature.

## 3. Gate scorecard (GATE-AM-S3-ACTION)
Action e2e on FP8 off the quantized-only checkpoint ✓ (P1/P2, all 3 v1 modes) · `t2i` non-regressed ✓
(P2, INV-2) · CPU suite green ✓ (exit 0) · `openapi.json` unchanged ✓ (INV-8) · no BF16 on the action
path ✓ (INV-4, `docker compose … config`) · residency safety net held ✓ (INV-5, 14.3 GiB, one plane) ·
no re-export (E-06 refuted, R-10 N/A) · owner action-quality **PASS** (Feng, 2026-07-25 — all three v1
modes judged good in the Action tab; INV-6 satisfied → action is now GPU-verified on FP8; default-on
stays AM-S4 per INV-7). Sharded review: 1 Medium correctness **fixed** + regression-tested; 2
maintainability **deferred** with rationale. Adversarial verifier: **PASS** (independent).

## 4. Scope adaptation (recorded, not silent)
The blueprint framed action as a checkpoint-**packaging** task with a likely `(c)` third-plane fallback;
the AM-S1 refutation (E-06) + the AM-S3 spike (a2) reduced it to **api-side serving wiring** off the
resident omni model. The owner-approved `(c)` `Plane.ACTION` (design D3) was therefore **not built**
(recorded in `design.md`'s spike-outcome banner + `brainstorming.md`). Docs consolidated to the lean
AM-S1/S2 set (brainstorming/design/decision_record/execution_contract + review/adversarial), per the
owner's spike-lean-docs preference (noted in `design.md`).

**Owner-authorized blast-radius amendment (2026-07-25, post-gate).** During the owner's quality-gate run,
the WebUI Action tab's "Run demo" was found unable to complete any job (it sent no conditioning; R-12).
The owner authorized fixing it — an explicit extension into otherwise-forbidden `webui/**`:
`webui/components/action-viewer/demoBody.ts` + `ActionWorkspace.tsx` now attach the checkpoint's shipped
example conditioning per mode, and `deploy/docker-compose.base.yml` adds `COSMOS3_INPUT_ALLOWLIST`
(artifact volume + the read-only `assets/` mount) so the api trusts those demo inputs. Verified: TDD
`demoBody.test.ts` (5), `tsc` clean, full webui suite 218 green, CPU suite green (incl. the private-ref
scan that caught + forced removal of an absolute path in the runbook), `openapi.json` unchanged (INV-8).
The `image_path`+allowlist→trajectory mechanism is GPU-proven (P2); the in-container click-through is the
AM-S4 all-modes smoke.

## 5. Handoff
See `docs/handoff.md`: (1) owner runs `OWNER-AM-ACTION-QUALITY` on the v1 demos; (2) AM-S4 default-on +
full-stack all-modes smoke + AM-S2 fork/overlay cleanup; (3) AM-S5 NVFP4 action.
