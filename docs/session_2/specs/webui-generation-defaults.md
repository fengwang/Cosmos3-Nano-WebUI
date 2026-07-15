# Capability: webui-generation-defaults

Status: MODIFIED (UX-S2)
Refs: FR-4, FR-5, INV-5; `EV-UX-RESOLUTION-DEFAULT-VIDEO-720`.

The WebUI default-selected preset for the (video) initial draft becomes
`hi-720`, and the negative-prompt field shows a "using recommended default"
affordance. `standard-480` and the full resolution picker remain available.

## MODIFIED Requirements

### Requirement: Video default preset is hi-720

The WebUI initial draft SHALL default to the `hi-720` preset (1280×720, 49
frames), so the default-selected video preset agrees with the server video
default (1280×720). The `standard-480` preset and the full resolution picker
SHALL remain available and selectable (INV-5).

#### Scenario: Initial draft selects hi-720

- WHEN a fresh studio draft is created (`initialDraft()`)
- THEN its selected preset SHALL be `hi-720` with params height 720, width 1280,
  num_frames 49

#### Scenario: standard-480 remains available

- WHEN the preset catalog / picker is rendered
- THEN both `standard-480` and `hi-720` SHALL be offered, and applying
  `standard-480` SHALL set 640×480 / 33 frames

#### Scenario: Server video default and UI default preset agree

- WHEN the UI default preset (`hi-720`) is active for a video mode
- THEN the dimensions it submits (1280×720) SHALL equal the server's mode-aware
  video default (1280×720)

### Requirement: Negative-prompt recommended-default affordance

The negative-prompt input SHALL display a "using recommended default" placeholder
indicating that leaving it blank applies the server's curated default. A typed
value SHALL still be sent and override the default; a blank value SHALL be
omitted from the request so the server default applies (INV-5).

#### Scenario: Placeholder communicates the recommended default

- WHEN the Compose panel renders with an empty negative-prompt field
- THEN the field SHALL show a placeholder conveying that a recommended default is
  used when left blank

#### Scenario: Blank negative prompt is omitted from the request

- WHEN a draft has an empty negative prompt
- THEN the built request SHALL omit `negative_prompt` (so the server applies its
  curated default)

#### Scenario: Typed negative prompt is sent and overrides

- WHEN a draft has a non-empty negative prompt
- THEN the built request SHALL include that `negative_prompt` value (overriding
  the server default)
