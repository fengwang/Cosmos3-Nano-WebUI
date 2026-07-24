# P5/P6 Evidence — Action serving via `vllm-omni` (a) and `diffusers_action` (c)

Date: 2026-07-24. Owner-chosen depth: **characterize + feasibility-load** (no
quality-judged trajectory run — that is AM-S3).

## Option (a) — `vllm-omni` action surface
The omni server registers a robot-policy WebSocket endpoint
**`/v1/realtime/robot/openpi`** (endpoint `realtime_robot_openpi`, logged via
`launcher.py:57`; not in the HTTP openapi paths — it is a WebSocket route).
Liveness probe (WS upgrade handshake):
- `HTTP/1.1 101 Switching Protocols` + valid `Sec-WebSocket-Accept` → the route is
  **genuinely registered and live** (a bogus sibling route returns **404**).
- On connect the server immediately sends:
  `{"type":"error","error":"Robot policy not available","code":"unsupported"}`.

⇒ **The action (a) surface EXISTS (contradicting E-07's "action is not a standard
OpenAI surface / likely absent"), but the robot policy is NOT loaded in this
serving configuration** — action (a) is present-but-not-functional as-served.
Wiring it (a serving flag / policy model / routing the checkpoint's action weights
into the openpi policy runtime) is an **AM-S3 investigation**. Note the API-shape
gap: the WebUI action tab calls REST `/v1/action/{forward_dynamics,inverse_dynamics,
policy}` (E-12), whereas the omni surface is a WebSocket **openpi realtime** stream —
AM-S3 must bridge these.

## Option (c) — in-process `diffusers_action` graft (feasibility-load)
Ran the **actual repo function** `engines.diffusers_action.loader.merge_state_dicts`
with the real key sets (checkpoint gen keys ∪ base action adapters), torch-free:

```
checkpoint gen tensors: 1246 (action_ among them: 5)
base action adapters to graft: [action_modality_embed, action_proj_in.{bias,fc}.weight, action_proj_out.{bias,fc}.weight]
GEN_TOWER_QUANTIZED = 505 (actual F8 tensors in checkpoint = 216)
merge_state_dicts RAISED: ValueError -> action graft key collision (GEN ∩ adapters): [the 5 action keys]
```

⇒ **The in-process (c) loader CANNOT instantiate on the current checkpoint.** The
load path (`load_action_transformer`) fails **CPU-side at step 5** (before any GPU
work) because the checkpoint **already contains** the 5 `action_*` tensors the code
tries to graft from the BF16 base → `merge_state_dicts` collision. A second,
independent incompatibility: `verify_precision(expected_quantized=505)` ≠ the actual
216 (drift D1, revision-independent). So the "feasibility-load" result is a
**definitive negative**: the (c) code assumes the E-06 gap that does not exist, and
must be fixed (drop the base graft; use the checkpoint's own action tensors) before
(c) can serve action. (Full GPU instantiation is moot — the failure precedes it.)

## Zero-BF16 action
The quantized FP8 (and NVFP4) checkpoints **already bundle** the BF16 `action_*`
adapters with `action_gen: true` and real values (P1). So **zero-BF16 action is
achieved at the checkpoint level — no re-export/packaging is required** (R-01/S-E
dissolve). The remaining work is purely **serving-path** (option (a) wiring, or a
(c) code fix), not checkpoint-packaging.

## Verdict (rubric)
- **Action mechanism: (a) preferred but currently non-functional; (c) broken
  as-coded.** Neither works as-served today. AM-S3 = serving-path work off the
  checkpoint's own action weights; recommend pursuing (a) (keeps one resident omni
  model → Studio+Action plane-merge) with (c) as a fallback that needs a code fix.
- **Zero-BF16 action packaging: NOT NEEDED** (tensors already bundled).

## Method notes (P6 was CPU-side; P4 not run)
- **P6**: the pre-registered GPU instantiation was **not performed** — the failure
  (`merge_state_dicts` key collision) occurs **CPU-side, before any GPU work**, by
  running the *actual repo function* on the real key sets (torch-free). The
  `GEN_TOWER_QUANTIZED=505 ≠ 216` precision mismatch is therefore **inferred** (the
  collision precedes the precision check), not executed at runtime.
- **P4** (reasoning-(c) standalone quantized reasoner) was **not run**: P3 found a
  chat surface (image-bound), so design's "only if P3 has no chat surface" branch
  did not fire; a second omni instance is the same fork → same image-gen behavior.
  The optional non-`--omni` arch check is deferred to AM-S2.

## Receipts (verbatim)
```
# (a) robot WS surface (option-a liveness):
$ curl -i -N -H "Upgrade: websocket" -H "Connection: Upgrade" \
    -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" -H "Sec-WebSocket-Version: 13" \
    http://127.0.0.1:8000/v1/realtime/robot/openpi
HTTP/1.1 101 Switching Protocols
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
<ws frame>  {"type":"error","error":"Robot policy not available","code":"unsupported"}
$ curl .../v1/realtime/robot/DOESNOTEXIST      ->  HTTP 404   (route genuinely registered)
# (c) in-process graft — real repo fn on real key sets, torch-free:
merge_state_dicts RAISED: ValueError -> action graft key collision (GEN ∩ adapters):
  ['action_modality_embed','action_proj_in.bias.weight','action_proj_in.fc.weight',
   'action_proj_out.bias.weight','action_proj_out.fc.weight']
GEN_TOWER_QUANTIZED = 505   (checkpoint actual F8_E4M3 = 216)
```
