"""AM-S5 action probe: drive the REAL vllm_omni_work against the NVFP4 omni container (:8020).

Mirrors AM-S3 P2 (production wiring, shipped assets) but on the NVFP4 checkpoint. Conditioning media
(first-frame png, av input mp4) are taken from the FP8 assets dir because the NVFP4 checkpoint's assets/
ships only outputs, not these inputs (a gap flagged for the wiring). Action chunk array from the shipped
example_action_fd_agibotworld_action_chunks.json (present in both).
"""
from __future__ import annotations
import json, os, sys, traceback

BASE = "http://127.0.0.1:8020"
FP8 = "/data/models/Cosmos3-Nano-FP8-Blockwise/assets"
NVFP4 = "/data/models/Cosmos3-Nano-NVFP4-Blockwise/assets"
S = os.environ.get("AMS5_SCRATCH", os.path.join(os.getcwd(), "scratch", "ams5"))  # override via AMS5_SCRATCH (INV-1: no private path committed)

os.environ.setdefault("ARTIFACTS_DIR", S + "/artifacts")
os.makedirs(os.environ["ARTIFACTS_DIR"], exist_ok=True)
# Trust the shipped-asset dirs as conditioning sources (mirrors the edge allowlist).
os.environ["COSMOS3_INPUT_ALLOWLIST"] = os.pathsep.join([FP8, NVFP4, os.environ["ARTIFACTS_DIR"]])
os.environ["COSMOS3_CHECKPOINT_LABEL"] = "nvfp4"  # so meta.precision == nvfp4

sys.path.insert(0, os.path.join(os.getcwd(), "api"))

from app.schemas import JobStatus  # noqa: E402
from engines.vllm_omni import work as vw  # noqa: E402
from jobs.model import JobRecord  # noqa: E402
from orchestrator.planes import Plane  # noqa: E402


def _first_chunk_16x29(path):
    raw = json.load(open(path))
    def dig(o):
        if isinstance(o, dict):
            for k in ("action_chunks", "actions", "chunks", "data"):
                if k in o:
                    return dig(o[k])
            return dig(list(o.values())[0])
        return o
    o = dig(raw)
    # o is either [chunks][frames][dim] or [frames][dim]
    if o and isinstance(o[0], list) and o[0] and isinstance(o[0][0], list):
        o = o[0]  # first chunk
    chunk = [list(map(float, row[:29])) for row in o[:16]]
    return chunk


def rec(mode, **params):
    return JobRecord(id=f"probe-{mode}", mode=mode, plane=Plane.GENERATION,
                     status=JobStatus.running, created_at="2026-07-26T00:00:00Z", params=params)


def run(label, record):
    print(f"\n===== {label} =====", flush=True)
    try:
        res = vw.vllm_omni_work(record, lambda f: None, base_url=BASE)
        p = res.artifact_path
        size = os.path.getsize(p) if os.path.exists(p) else -1
        head = open(p, "rb").read(12) if size > 0 else b""
        print(f"PASS  artifact={p}  size={size}  head={head[:8].hex()}  meta={ {k:res.meta.get(k) for k in ('engine','precision','action_mode','trajectory_path')} }", flush=True)
        traj = res.meta.get("trajectory_path")
        if traj and os.path.exists(traj):
            t = json.load(open(traj))
            arr = t if isinstance(t, list) else t.get("data", t)
            import numpy as np
            a = np.array(arr)
            print(f"      trajectory sidecar shape={a.shape}", flush=True)
        if p.endswith(".json"):
            t = json.load(open(p))
            arr = t if isinstance(t, list) else t.get("data", t)
            import numpy as np
            a = np.array(arr)
            print(f"      trajectory artifact shape={a.shape}", flush=True)
        return True
    except Exception as e:
        print(f"FAIL  {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        return False


results = {}
# forward_dynamics (sync): agibotworld 29-D, given a 16x29 action chunk + first-frame image
chunk = _first_chunk_16x29(f"{NVFP4}/example_action_fd_agibotworld_action_chunks.json")
results["forward_dynamics"] = run("forward_dynamics (agibotworld, sync /v1/videos/sync)", rec(
    "forward_dynamics", prompt="Pickup items in the supermarket", domain_name="agibotworld",
    chunk_size=16, raw_action_width=29, raw_actions=chunk, resolution_tier=480,
    image_path=f"{FP8}/example_action_fd_agibotworld_first_frame.png"))

# policy (async predict): agibotworld 29-D, first-frame image -> predicted [16,29] + rollout
results["policy"] = run("policy (agibotworld, async /v1/videos)", rec(
    "policy", prompt="Pickup items in the supermarket", domain_name="agibotworld",
    chunk_size=16, resolution_tier=480,
    image_path=f"{FP8}/example_action_fd_agibotworld_first_frame.png"))

# inverse_dynamics (async predict): av 9-D, input clip -> recovered [60,9]
results["inverse_dynamics"] = run("inverse_dynamics (av, async /v1/videos)", rec(
    "inverse_dynamics", prompt="drive", domain_name="av", chunk_size=60, resolution_tier=480,
    video_path=f"{FP8}/example_action_id_av_0_input.mp4"))

print("\n===== SUMMARY =====")
for k, v in results.items():
    print(f"  {k}: {'PASS' if v else 'FAIL'}")
sys.exit(0 if all(results.values()) else 1)
