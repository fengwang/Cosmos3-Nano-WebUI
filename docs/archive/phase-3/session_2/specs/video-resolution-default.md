# Capability: video-resolution-default

Status: MODIFIED (UX-S2)
Refs: FR-5, INV-5, INV-6, INV-8, INV-P5-1, R-06, E-07;
`EV-UX-RESOLUTION-DEFAULT-VIDEO-720`.

The server default resolution becomes mode-aware: video modes default to
1280×720 when dimensions are omitted; `t2i` is unchanged; explicit dimensions
still override.

## MODIFIED Requirements

### Requirement: Mode-aware server default dimensions

When a generation request omits `width`, `height`, and `resolution`, the server
default dimensions SHALL depend on the mode: video modes (`t2v`, `i2v`,
`t2v_audio`) SHALL default to width 1280 × height 720; `t2i` SHALL default to
480 × 480 (unchanged). This mode-aware default SHALL be applied in the engine
server-default path (`resolved_params` for the deployed vLLM-Omni path and
`_to_generation_request` for the dormant diffusers path) so that API-only
clients — not just the WebUI — receive the video default. The resolved
dimensions SHALL remain the single source shared by the submitted request and
the recorded job metadata (INV-P5-1).

#### Scenario: Video mode omitting dimensions defaults to 1280×720

- WHEN a `t2v` (or `i2v`, or `t2v_audio`) request omits `width`, `height`, and
  `resolution`
- THEN the resolved size SHALL be 1280×720

#### Scenario: Image mode omitting dimensions is unchanged

- WHEN a `t2i` request omits `width`, `height`, and `resolution`
- THEN the resolved size SHALL be 480×480 (the text→image default is unchanged)

#### Scenario: Recorded metadata matches the submitted dimensions

- WHEN a video request omitting dimensions is submitted
- THEN the width/height in the recorded job metadata SHALL equal the width/height
  in the submitted engine request (no desync; both 1280×720)

### Requirement: Explicit dimensions and resolution remain authoritative

An explicitly supplied `width`/`height`, or an explicitly supplied square
`resolution`, SHALL override the mode-aware default. No preset SHALL remove the
caller's ability to choose dimensions (INV-5). The public request/response schema
shape SHALL NOT change; only default values and the `resolution` field
description change (INV-6).

#### Scenario: Explicit width/height win over the video default

- WHEN a `t2v` request supplies `width=640` and `height=480`
- THEN the resolved size SHALL be 640×480 (not the 1280×720 default)

#### Scenario: Explicit square resolution wins over the video default

- WHEN a `t2v` request supplies `resolution=480` (and omits width/height)
- THEN the resolved size SHALL be 480×480 (the explicit square value is honored)

#### Scenario: A t2i request may still request 720 explicitly

- WHEN a `t2i` request supplies `resolution=720`
- THEN the resolved size SHALL be 720×720 (image callers keep full choice)

### Requirement: Quantized-only 720p posture is preserved

The 720p video default SHALL be served only by the quantized FP8/NVFP4 generation
path (the deployment fact), never the BF16 base. A heavier-than-default
configuration SHALL surface a documented advisory rather than a silent OOM
(INV-8); this session adds no new server advisory logic but preserves the
existing 720p preset advisory and records the R-05 residual VRAM caveat.

#### Scenario: 720p default coincides with the quantized deployment

- WHEN the video 720p default is served
- THEN it SHALL be served by the deployed quantized checkpoint (FP8 or NVFP4),
  consistent with the single-checkpoint deployment, never the BF16 base
