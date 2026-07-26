# Walkthrough — see each mode in action

**TL;DR:** bring up one stack, open the web app, and run each mode once. Every example below runs on
the single quantized checkpoint you already downloaded — no extra models, no keys. Follow the steps,
then drop your own screenshot into `docs/images/` where each placeholder points.

Every mode here is **GPU-verified on both FP8 and NVFP4** with the owner's manual quality PASS — the
expected outputs are written against those real runs (see [`docs/evidence_map.md`](docs/evidence_map.md)),
not guessed. No performance numbers are promised.

**Jump to:** [Setup once](#setup-once) · [Studio](#studio) · [Reasoning](#reasoning) · [Action](#action)

> **Before you start.** This is a trusted-LAN / lab-box appliance: **no login**, ports bind to
> `localhost`, and content **guardrails are off** by design, so output is unfiltered. Full posture is in
> the README [Status & security](README.md#status--security) section.

## Setup once

Bring up one stack (FP8 shown; `make up-nvfp4` is identical), wait for health, and open the web app.
A plain `make up-fp8` starts **all three modes** off the quantized-only checkpoint — there is no BF16
base and no reasoning overlay to add.

```bash
make up-fp8        # or: make up-nvfp4  — run one stack at a time
make health        # wait for {"status":"ready"}
# open http://localhost:3000  (you land in the Studio)
```

The first request of a mode cold-starts its backend (the orchestrator swaps residency on demand and
keeps the model warm for 30 min), so give the very first generation a minute.

## Studio

The Studio is the landing page: type a prompt, pick a stage, and generate. Studio covers **text→image**
and the video modes **text→video**, **image→video**, and **video+audio**.

### Text → image (the quickstart example)

1. Open **Studio** (the home page, `/studio`).
2. In the prompt box, type: **`a red apple on a wooden table, studio photo`**.
3. Keep the default size **480×480** and click **Generate**.
4. In a few seconds a clean, studio-lit image of a red apple on a wooden table appears in the gallery.

**Expected:** one 480×480 PNG, coherent and on-prompt (this is the end-to-end `t2i` path GPU-verified
under `GPU-S3` on both FP8 and NVFP4).

![Studio text→image: a red apple on a wooden table](docs/images/studio-t2i.png)

### Text → video, image → video, video + audio

1. In **Studio**, switch the stage to **Video** (or **Image→Video** / **Video+Audio**).
2. For text→video, enter a prompt such as **`a paper boat drifting down a rain-filled gutter, close-up`**;
   for image→video, upload a start frame; for video+audio, use a prompt with sound, e.g.
   **`waves breaking on a rocky shore at sunset`**.
3. Keep the default **1280×720**, 49-frame output and click **Generate**.

**Expected:** a ~1280×720 clip (about 49 frames) that follows the prompt; **video+audio** adds a matching
soundtrack. All three video modes are GPU-verified on both FP8 and NVFP4 with the owner's quality PASS
(2026-07-26). Prefer **NVFP4** for more VRAM headroom at higher frame counts.

![Studio text→video result](docs/images/studio-t2v.png)
![Studio image→video result](docs/images/studio-i2v.png)
![Studio video+audio result](docs/images/studio-t2v_audio.png)

<details>
<summary>Reproduce via the API</summary>

The Studio posts to the app API (`POST /v1/generation/t2i` and the `t2v`/`i2v`/`t2v_audio` variants);
exact request bodies and the underlying `vllm-omni` serving command are in
[`docs/model_setup.md`](docs/model_setup.md) (§6, §9). The `t2i` non-regression example prompt is
`"a red apple on a wooden table, studio photo"` at `480x480`.
</details>

## Reasoning

The **Reasoning** tab (`/chat`) is a streaming chat surface served by the quantized understanding tower
(zero BF16) — no separate base model.

1. Open the **Reasoning** tab.
2. Type a question, e.g. **`List three primary colors, comma-separated.`** and send it.
3. The answer streams back token by token.

**Expected:** a coherent, on-topic answer — for the example above, `Red, Blue, Yellow`. Multi-step
questions work too: the recorded all-modes run answered a robotics prompt with *"…the lack of friction
between the gripper and the cup's surface reduces the grip strength needed to hold it securely."*
Reasoning is GPU-verified with the owner's quality PASS on FP8 (`AM-S2`) and NVFP4 (`AM-S5`).

![Reasoning: a streamed answer in the chat tab](docs/images/reasoning-chat.png)

<details>
<summary>Reproduce via the API</summary>

Reasoning is served over `POST /v1/reason` (OpenAI-compatible streaming). Serving details (the
`vllm-reasoner` container, `--quantization fp8_blockwise_w8a16` / `nvfp4_blockwise_w4a16`, zero BF16) are
in [`docs/model_setup.md`](docs/model_setup.md) §6.
</details>

## Action

The **Action** tab (`/action`) drives the robot world model. The shipped demo carries the checkpoint's
example conditioning inputs, so you can run each mode with one click.

### Forward dynamics (agibotworld, 29-D) — the worked example

1. Open the **Action** tab.
2. Set **Embodiment** to **`agibotworld (29-D, 3D)`** and **Mode** to **`Forward dynamics`**.
3. Click **Run demo**.
4. Watch the status go *running → succeeded* (elapsed readout, with a Cancel control), then the result
   region shows a **live 3D robot view** animating the rollout, alongside 2D trajectory plots and an
   inspection panel.

**Expected:** a short rolled-out MP4 (~0.6 MB, 17 frames at 10 fps) plus a 3D robot animation of the
agibotworld arm following the demo action chunk — GPU-verified on FP8 (`AM-S3`) and NVFP4 (`AM-S5`) with
the owner's quality PASS.

![Action forward_dynamics: 3D robot rollout](docs/images/action-forward_dynamics.png)

### The other two demos (also owner-verified)

- **Policy** (agibotworld, 29-D): Embodiment `agibotworld` + Mode **`Policy`** → **Run demo** → a
  predicted `[16, 29]` action trajectory **and** a rollout video, shown in the 3D view.
  ![Action policy: predicted trajectory + rollout](docs/images/action-policy.png)
- **Inverse dynamics** (av, 9-D): Embodiment **`av (9-D, 2D plots)`** + Mode **`Inverse dynamics`** →
  **Run demo** → a recovered `[60, 9]` action trajectory, shown as **2D trajectory plots** (no 3D view
  for `av`).
  ![Action inverse_dynamics: 2D trajectory plots](docs/images/action-inverse_dynamics.png)

<details>
<summary>Reproduce via the API</summary>

Action is served through the `vllm-omni` video API (`POST /v1/action/{forward_dynamics,inverse_dynamics,policy}`
at the app layer; `forward_dynamics` = sync `/v1/videos/sync`, `policy`/`inverse_dynamics` = async
`/v1/videos`). The exact request bodies, shipped example inputs, and a copy-paste runbook are in
[`docs/session_3/action_demo_runbook.md`](docs/session_3/action_demo_runbook.md).
</details>
