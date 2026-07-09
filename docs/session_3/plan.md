# Session 3 Plan - Joint Validation on RTX 5090

Date: 2026-07-09

Confirmed API shapes used below (read from `api/app/routes/generation.py`,
`api/app/jobs_router.py`, `api/app/auth.py`, `api/engines/vllm_omni/client.py`
— read-only reference, none of it is edited this session):

- **Full-stack:** header `X-API-Key` (checked against `COSMOS3_API_KEY`);
  `POST /v1/generation/t2i` body `{"prompt", "seed", "resolution"}` -> `202`
  `Job{id, status, ...}`; poll `GET /v1/jobs/{id}` until `status` in
  `{succeeded, failed, cancelled}`; fetch `GET /v1/jobs/{id}/artifact`.
- **Direct (T2I):** vLLM-Omni's own OpenAI-images-compatible endpoint,
  `POST /v1/images/generations` JSON body
  `{"prompt", "size": "WxH", "n": 1, "response_format": "b64_json",
  "num_inference_steps", "guidance_scale", "seed"}` -> `{"data":
  [{"b64_json": "..."}]}`.
- **Direct (T2V):** vLLM-Omni's async video endpoint,
  `POST /v1/videos` multipart form `{"prompt", "size", "num_frames", "fps",
  "num_inference_steps", "guidance_scale", "flow_shift", "seed",
  "max_sequence_length", "extra_params": json({"use_resolution_template":
  false, "use_duration_template": false, "guardrails": false})}` -> poll
  `GET /v1/videos/{id}` until `status in {completed, failed}` -> download
  `GET /v1/videos/{id}/content`.
- The `vllm-omni` service's port 8000 is **not** published to the host by
  `deploy/docker-compose.fp8.yml`/`.nvfp4.yml` (only `api`'s is) — direct
  calls run from inside the compose network via
  `docker compose exec vllm-omni <curl-or-python> http://localhost:8000/...`.
  Confirm at task 5.1 whether `curl` is present in the `vllm/vllm-openai`
  base image; fall back to `python3 -c '...urllib...'` (stdlib only,
  mirroring `UrllibVideoTransport`'s own approach) if not.

Probe scripts do **not** import from `api/**` — they reuse the request
*shape* documented above but stay self-contained, so this session never
takes a code dependency on the forbidden blast-radius surface.

## Task 2 — Probe library

**Test first** (`docs/session_3/probes/test_lib.py`):

```python
from lib import Verdict, check_no_lfs_pointers, check_valid_image, FileInfo

def test_check_no_lfs_pointers_flags_a_pointer_file():
    files = (FileInfo(path="a.json", size=120, is_lfs_pointer=False),
             FileInfo(path="model.safetensors.index.json", size=45, is_lfs_pointer=True))
    assert check_no_lfs_pointers(files) == Verdict.FAIL

def test_check_no_lfs_pointers_passes_when_clean():
    files = (FileInfo(path="a.json", size=120, is_lfs_pointer=False),)
    assert check_no_lfs_pointers(files) == Verdict.PASS

def test_check_valid_image_rejects_non_image_bytes():
    assert check_valid_image(b"not an image", expected_dims=None) == Verdict.FAIL
```

This is a real failing test before `lib.py` exists — run
`uv run pytest docs/session_3/probes/test_lib.py -v` and confirm it fails on
import, then implement.

**Implementation** (`docs/session_3/probes/lib.py`):

```python
from dataclasses import dataclass
from enum import Enum, auto

class Verdict(Enum):
    PASS = auto()
    FAIL = auto()
    SCOPED_OUT = auto()

@dataclass(frozen=True)
class FileInfo:
    path: str
    size: int
    is_lfs_pointer: bool

@dataclass(frozen=True)
class EvidenceRecord:
    task_id: str
    hardware: str
    driver_cuda: str
    checkpoint_repo: str
    checkpoint_revision: str
    vllm_omni_commit: str
    request_shape: dict
    artifact_path: str | None
    artifact_metadata: dict | None
    verdict: Verdict
    notes: str = ""

def check_no_lfs_pointers(files: tuple[FileInfo, ...]) -> Verdict:
    """No file in `files` is an unresolved LFS/Xet pointer. Pure — no filesystem access here."""
    return Verdict.FAIL if any(f.is_lfs_pointer for f in files) else Verdict.PASS

def check_no_stale_index(files: tuple[FileInfo, ...]) -> Verdict:
    """No top-level `model.safetensors.index.json` is present. Pure."""
    stale = any(f.path == "model.safetensors.index.json" for f in files)
    return Verdict.FAIL if stale else Verdict.PASS

def check_valid_image(image_bytes: bytes, expected_dims: tuple[int, int] | None) -> Verdict:
    """Decode-and-check via stdlib-only signature sniffing; `expected_dims` optional. Pure."""
    ...  # PNG/JPEG magic-byte + (optional) dimension check; no I/O

def check_job_terminal(status_history: tuple[str, ...]) -> Verdict:
    """Pure: PASS iff the last status is 'succeeded', FAIL if 'failed'/'cancelled' or never terminal."""
    ...

def check_image_freshness(dockerfile_mtime: float, image_created_at: float) -> Verdict:
    """Pure: PASS iff the cached image is newer than the Dockerfile it should reflect."""
    return Verdict.PASS if image_created_at >= dockerfile_mtime else Verdict.FAIL

def build_evidence_record(**kwargs) -> EvidenceRecord:
    """Pure constructor; raises ValueError if verdict != PASS and notes is empty (Check 5/aggregate boundary)."""
    ...
```

Run: `uv run pytest docs/session_3/probes/test_lib.py -v` (must be all green,
no GPU/network involved). **Commit point:** `feat(gpu-s3): probe library
(lib.py) + unit tests`.

## Task 3 — T1 fresh checkpoint fetch

`docs/session_3/probes/run_checkpoint_fetch.py --checkpoint {fp8,nvfp4}`:

1. Action: `hf download wfen/Cosmos3-Nano-{FP8,NVFP4}-Blockwise --revision
   <GPU-S2 sha> --local-dir models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise`.
2. Action: walk the downloaded directory -> `tuple[FileInfo, ...]` (size +
   a pointer-shaped-content sniff per byte-prefix `version https://git-lfs`).
3. Calculation: `check_no_lfs_pointers` + `check_no_stale_index` on that
   tuple.
4. Action: write `evidence_checkpoint_fetch_{checkpoint}.json`.

Run for FP8, then NVFP4. **Commit point:** `feat(gpu-s3): T1 fresh checkpoint
fetch probe + evidence`.

## Task 4 — T2 image freshness

Inline in `run_direct_t2i.py`'s setup, not a separate script (it's a
one-line gate, not an independent deliverable): `git diff --quiet HEAD --
deploy/vllm-omni.Dockerfile` (exit code) -> `check_dockerfile_unmodified`.
If dirty, stop — this session cannot edit that file, so a diff means
something unexpected happened outside this session's control (not a
"rebuild and continue" case). If clean, reuse
`cosmos3-nano-vllm-omni:local`.

(mtime-vs-`Created` comparison was the original design; superseded during
T2 execution — see `design.md` D3 — because `git checkout` bumps mtimes on
branch switch independent of content.)

## Task 5 — T3/T4 direct T2I

`docs/session_3/probes/run_direct_t2i.py --checkpoint {fp8,nvfp4}`:

1. Action: `make up-{fp8,nvfp4}` (or the compose invocation directly).
2. Action: wait for `/v1/models` (or the container's own readiness) to
   respond, bounded timeout.
3. Action: `docker compose exec vllm-omni <post images/generations>` with
   the confirmed direct-T2I body above (resolution 480, matching the
   documented supported set); decode the returned base64 to bytes.
4. Calculation: `check_valid_image(bytes, expected_dims=(480, 480))`.
5. Calculation: `build_evidence_record(...)`.
6. Action: write `evidence_direct_t2i_{checkpoint}.json`; `make down`.

Run for FP8, then NVFP4 (never both stacks up at once). **Commit point:**
`feat(gpu-s3): T3/T4 direct T2I probes + evidence (fp8, nvfp4)`.

## Task 6 — T5/T6 full-stack T2I

`docs/session_3/probes/run_fullstack_t2i.py --checkpoint {fp8,nvfp4}`:

1. Action: `make up-{fp8,nvfp4}` (api + vllm-omni both up; api already reads
   `COSMOS3_API_KEY` from `.env`).
2. Action: `POST /v1/generation/t2i` with `X-API-Key: $COSMOS3_API_KEY`,
   body `{"prompt": ..., "seed": ..., "resolution": 480}`.
3. Action: poll `GET /v1/jobs/{id}` until terminal, bounded timeout.
4. Calculation: `check_job_terminal(status_history)`.
5. Action (only if terminal=succeeded): `GET /v1/jobs/{id}/artifact`;
   Calculation: `check_valid_image`.
6. Calculation: `build_evidence_record(...)`.
7. Action: write `evidence_fullstack_t2i_{checkpoint}.json`; `make down`.

Run for FP8, then NVFP4. **Commit point:** `feat(gpu-s3): T5/T6 full-stack
T2I probes + evidence (fp8, nvfp4)`.

## Task 7 — T7 T2V smoke

`docs/session_3/probes/run_t2v_smoke.py`:

1. Action: `make up-nvfp4`.
2. Action: direct `POST /v1/videos` (multipart, per the confirmed shape
   above), 256x256, minimal `num_frames` (e.g. 9), poll `GET
   /v1/videos/{id}` with a tighter timeout than the T2I probes (a smoke, not
   a full run).
3. On success: Calculation validates the returned bytes look like a video
   container (magic bytes), `Verdict.PASS`.
4. On any failure (HTTP error, OOM signal in container logs, timeout):
   catch at the single narrow boundary, `Verdict.SCOPED_OUT` with `notes`
   stating the concrete reason. Only if the failure is unambiguously
   VRAM-related, retry once with FP8 instead of NVFP4 before recording
   `SCOPED_OUT`.
5. Action: write `evidence_t2v_smoke.json` regardless of branch taken;
   `make down`.

**Commit point:** `feat(gpu-s3): T7 T2V smoke probe + evidence`.

## Task 8 — Evidence aggregation and doc sync

`docs/session_3/probes/aggregate.py`: pure merge of every
`evidence_*.json` fragment present into `evidence.json` (report missing
task IDs, per the `evidence-aggregation` spec) + `summary.md`. Then, driven
by that merged evidence (never invented ahead of it):

- `docs/evidence_map.md` — append the GPU-S3 rows in the file's existing
  format.
- `docs/eval_seed_cases.md` — update the four `EV-GPU-*` rows' results.
- `docs/model_setup.md` §6/§8, `docs/release_checklist.md` §7, `README.md`
  — flip FP8/NVFP4 `t2i` to "T2I-verified" only where the evidence is
  `PASS`, citing the evidence_map row.
- `docs/risk_register.md` — close R-05/R-09 or add a new row per the
  `risk-and-eval-case-closure` spec.

**Commit point:** `docs(gpu-s3): evidence aggregation + per-mode/risk/eval
doc sync`.

## Task 9 — Review and verification

Sharded review (5 axes) -> fix High/Critical only -> re-run the affected
probe(s) -> adversarial verification. No plan-level code changes anticipated
here beyond fixes the review surfaces.

## Task 10 — Session close

`docs/handoff.md` from the template; eval seed harvest to
`docs/eval_corpus/`; final commit.
