# P7 Evidence — VRAM footprints + residency implication

Date: 2026-07-24. Hardware: RTX 5090, 32607 MiB total, sm_120, driver 610.43.03.
Samples via `nvidia-smi --query-gpu=memory.used --format=csv`.

## Measured footprints (FP8, `--no-guardrails --vae-use-tiling --enable-layerwise-offload`)
| State | GPU used |
|---|---|
| Idle (no container) | **18 MiB** |
| Loading (t≈15 s) | 4690 MiB |
| Loading (t≈30 s) | 13212 MiB |
| **Omni generation server resident** (ready) | **~13.2–13.5 GiB** |
| During `/v1/chat/completions` (image gen) | ~13.5 GiB |
| After `docker stop` (cleanup) | 18 MiB (no leak) |

The single omni server resident with the FP8 checkpoint = **~13.5 GiB of 32** →
large headroom. (Matches the UX-S2 note of ~14.7 GiB peak at the 720p default.)

## Built-in residency control
The omni server exposes `/v1/omni/sleep` and `/v1/omni/wakeup` (staged offload;
they require a `stage_ids` body — an AM-S4 detail). This is a **fork-native
residency mechanism** the orchestrator could use instead of, or alongside, its
current process-kill eviction (E-08/E-09) — a note for AM-S4.

## Residency implication (per mode)
- **Studio (generation):** served by the omni server, ~13.5 GiB resident.
- **Reasoning:** NOT served by the omni server (its chat = image gen, P3). So
  reasoning remains a **separate plane** → **swap retained** (evict-before-load,
  E-08/INV-5). Today's reasoner is the BF16 base (~26 GiB @ 0.85 util, E-08); a
  quantized reasoner (if ever achieved) would be cheaper, but reasoning still does
  **not** plane-merge with Studio.
- **Action:** if action (a) is wired into the omni server (robot policy off the
  checkpoint's own action weights), **Studio + Action share the SAME resident omni
  model → plane-merge (no extra VRAM, no swap).** This is the one genuine
  plane-merge opportunity this spike found — and it is **Studio+Action**, not the
  Studio+Reasoning merge the blueprint speculated about (project_contract §two-pass
  item 7 / R-08).
- **INV-5 safety net:** unchanged. No co-residency is assumed; the ~13.5 GiB Studio
  footprint leaves ample budget, and any future co-residency (e.g. a quantized
  reasoner beside Studio) must be VRAM-trace-verified before adoption.

## Receipts (raw `nvidia-smi`) + sample notes
```
$ nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
idle:               18 MiB, 32607 MiB
loading t≈15s:      4690 MiB
loading t≈30s:      13212 MiB
resident (ready):   13446 MiB
during image-gen:   13500 MiB
after docker stop:  18 MiB          # single stop cycle
```
Notes: the pre-registered sample (iv) "diffusers_action loaded" is **N/A** — the
(c) load aborts CPU-side (P6), so there is no GPU footprint to sample. Sample (iii)
is **image generation** (the omni "chat" output), not a text chat. "Returned to 18
MiB after stop" is one stop cycle, not a repeated-cycle leak test. The Studio+Action
plane-merge footprint (wired robot policy) is **unmeasured** — a projection to
verify in AM-S3.
