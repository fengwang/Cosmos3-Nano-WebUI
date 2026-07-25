# AM-S3 Action Demo Runbook (owner quality gate: OWNER-AM-ACTION-QUALITY)

Two ways to run the action demos on the FP8 stack. **Option B is exactly what I GPU-verified**
(`evidence/P1`, `P2`) and needs only the one omni container — use it if the full stack won't come up.
Docker + the GPU are required (the model is served by vLLM inside the container; there is no bare-metal path).

Set your checkpoint path once (the compose default `../models/...` is relative to `deploy/`; point it at
your real mount):

```bash
export COSMOS3_FP8_DIR=/data/models/Cosmos3-Nano-FP8-Blockwise   # your FP8 checkpoint dir
```

---

## Option A — Full stack + WebUI Action tab (intended end-user demo)

```bash
cd /path/to/Cosmos3-Nano-WebUI                   # your repo checkout
COSMOS3_FP8_DIR=$COSMOS3_FP8_DIR make up-fp8      # api + vllm-omni + vllm-reasoner + webui
make health                                       # wait until healthy
# open the WebUI (default http://localhost:3000) → Action tab → run forward_dynamics / policy / inverse_dynamics
make down                                         # stop everything when done
```

Caveat: the api starts/stops the omni container on demand via the mounted docker socket
(`/var/run/docker.sock`). That api-driven orchestration + the Studio↔Action residency handling is the
**AM-S4** full-stack smoke — plausible but **not verified in AM-S3**. If the Action tab errors or hangs,
use Option B (the serving path itself is proven).

---

## Option B — Direct omni container (proven; what AM-S3 GPU-verified)

### 1. Launch omni (off the quantized-only FP8 checkpoint)

```bash
docker rm -f cosmos3-action-demo 2>/dev/null
docker run -d --name cosmos3-action-demo --gpus all --shm-size 16g -p 8000:8000 \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  -v "$COSMOS3_FP8_DIR":/models/checkpoint:ro \
  cosmos3-nano-vllm-omni:local \
  vllm serve /models/checkpoint --omni --host 0.0.0.0 --port 8000 --init-timeout 1800 \
  --no-guardrails --vae-use-tiling --enable-layerwise-offload

# wait for readiness (~1 min): repeat until it prints 200
until curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/v1/models | grep -q 200; do sleep 5; done
```

### 2. Run all three demos with the checkpoint's shipped example inputs

Saves a rollout MP4 + trajectory JSON per mode to `./action_demo_out/` for you to inspect.

```bash
mkdir -p action_demo_out
ASSETS="$COSMOS3_FP8_DIR/assets" python3 - <<'PY'
import os, json, time, requests
A = os.environ["ASSETS"]; OUT = "action_demo_out"; BASE = "http://127.0.0.1:8000"

def poll(vid):
    while True:
        s = requests.get(f"{BASE}/v1/videos/{vid}", timeout=60).json()
        if s.get("status") in ("completed", "failed"):
            return s
        time.sleep(3)

# --- forward_dynamics (agibotworld 29-D): given a first frame + actions → roll out a video (sync) ---
spec = json.load(open(f"{A}/example_action_fd_agibotworld_action_chunks.json"))
r = requests.post(f"{BASE}/v1/videos/sync",
    data={"prompt": spec["prompt"], "size": "640x480", "num_frames": "17", "fps": "10",
          "num_inference_steps": "30", "guidance_scale": "1.0", "flow_shift": "5.0", "seed": "123",
          "extra_params": json.dumps({"action_mode": "forward_dynamics", "domain_name": "agibotworld",
              "raw_action_dim": 29, "action_chunk_size": 16, "action": spec["action_chunks"][0],
              "view_point": spec["view_point"]})},
    files={"input_reference": ("frame.png", open(f"{A}/example_action_fd_agibotworld_first_frame.png","rb"), "image/png")},
    timeout=600)
open(f"{OUT}/forward_dynamics_rollout.mp4","wb").write(r.content)
print("forward_dynamics ->", r.status_code, len(r.content), "bytes -> forward_dynamics_rollout.mp4")

# --- inverse_dynamics (av 9-D): given a video → recover the action trajectory (async, action-only) ---
sub = requests.post(f"{BASE}/v1/videos",
    data={"prompt": "recover the action trajectory", "num_frames": "61",
          "extra_params": json.dumps({"action_mode": "inverse_dynamics", "domain_name": "av",
              "raw_action_dim": 9, "action_chunk_size": 60})},
    files={"input_reference": ("clip.mp4", open(f"{A}/example_action_id_av_0_input.mp4","rb"), "video/mp4")},
    timeout=120).json()
res = poll(sub["id"]); traj = (res.get("action") or {}).get("data")
json.dump(traj, open(f"{OUT}/inverse_dynamics_trajectory.json","w"))
print("inverse_dynamics ->", res.get("status"), f"{len(traj)}x{len(traj[0])} -> inverse_dynamics_trajectory.json")

# --- policy (agibotworld 29-D): given an observation image → predict actions + a rollout video (async) ---
sub = requests.post(f"{BASE}/v1/videos",
    data={"prompt": "Pickup items in the supermarket", "size": "640x480", "num_frames": "17", "fps": "10",
          "num_inference_steps": "30", "guidance_scale": "1.0", "flow_shift": "5.0", "seed": "123",
          "extra_params": json.dumps({"action_mode": "policy", "domain_name": "agibotworld",
              "raw_action_dim": 29, "action_chunk_size": 16, "view_point": "concat_view"})},
    files={"input_reference": ("frame.png", open(f"{A}/example_action_fd_agibotworld_first_frame.png","rb"), "image/png")},
    timeout=120).json()
res = poll(sub["id"]); traj = (res.get("action") or {}).get("data")
json.dump(traj, open(f"{OUT}/policy_trajectory.json","w"))
vid = requests.get(f"{BASE}/v1/videos/{sub['id']}/content", timeout=120).content
open(f"{OUT}/policy_rollout.mp4","wb").write(vid)
print("policy ->", res.get("status"), f"{len(traj)}x{len(traj[0])} + {len(vid)}B video -> policy_*.{{json,mp4}}")
PY
```

### 3. Inspect + tear down

```bash
ls -la action_demo_out/          # 2 rollout MP4s + 2 trajectory JSONs (+ FD MP4) to judge quality
docker rm -f cosmos3-action-demo # free the GPU when done
```

Reference outputs shipped in the checkpoint for comparison: `assets/example_action_fd_agibotworld_4chunk_output.mp4`,
`assets/example_action_id_av_0_output.json`.

---

## Troubleshooting a failed launch

- **`make up-fp8` can't find the checkpoint** → set `COSMOS3_FP8_DIR` to the absolute mount path (above),
  or write a `deploy/.env`/`.env` and run `make up-fp8 ENV_FILE=.env`. Verify the resolved mount with
  `COSMOS3_FP8_DIR=$COSMOS3_FP8_DIR docker compose -f deploy/docker-compose.fp8.yml config` (look at the
  `vllm-omni` `source:` path).
- **docker permission denied** → your user must be in the `docker` group (per `ENVIRONMENTS.md`); re-login
  or `newgrp docker`. Confirm with `docker info`.
- **GPU not visible in the container** → the NVIDIA container toolkit must be installed; test with
  `docker run --rm --gpus all cosmos3-nano-vllm-omni:local nvidia-smi`.
- **port 8000 busy** → change `-p 8000:8000` to another host port and point the curls at it.
- **`requests` missing** for the Option B demo → `uv run --project api python - <<'PY' ...` (the api env has
  it) or `pip install requests`.
