# Capability: negative-prompt-default

Status: NEW (UX-S2)
Refs: FR-4, INV-1, INV-5, INV-6, R-03, R-04, E-04..E-06;
`EV-UX-NEGPROMPT-DEFAULT-APPLIED`, `EV-UX-NEGPROMPT-NO-ABS-PATH`.

The API applies the curated negative prompt from the model assets as an
overridable server-side default when a generation request omits
`negative_prompt`, degrading gracefully when the file is unavailable.

## ADDED Requirements

### Requirement: Configurable negative-prompt path resolution

The negative-prompt file path SHALL be derived from the configurable
`COSMOS3_MODEL_DIR` environment variable as `${COSMOS3_MODEL_DIR}/assets/
negative_prompt.json`. The loader module SHALL contain no hardcoded absolute
model path (no `/data/models` literal). When `COSMOS3_MODEL_DIR` is unset, the
loader SHALL resolve to "no default" rather than a baked-in absolute path.

#### Scenario: Path derives from the model-directory variable

- WHEN `COSMOS3_MODEL_DIR` is set to `/models/checkpoint`
- THEN the resolved path SHALL be `/models/checkpoint/assets/negative_prompt.json`

#### Scenario: No hardcoded absolute path in the loader

- WHEN the loader module source is scanned for `/data/models`
- THEN there SHALL be zero matches (the path is derived from the variable, INV-1)

#### Scenario: Unset variable yields no default rather than an absolute fallback

- WHEN `COSMOS3_MODEL_DIR` is not set in the environment
- THEN the loader SHALL return no default (`None`) and SHALL NOT read from any
  hardcoded absolute path

### Requirement: Overridable server-side default application

When a generation request omits `negative_prompt`, the API SHALL send the
file-sourced curated default to the engine. A user-supplied `negative_prompt`
SHALL override the default. The public request/response schema shape SHALL NOT
change (the field remains `negative_prompt: str | None`; INV-6).

#### Scenario: Default applied when the request omits the field

- WHEN a generation request is submitted with no `negative_prompt` and the
  curated file is present
- THEN the job params SHALL carry the file-sourced default as the
  `negative_prompt` value passed to the engine

#### Scenario: User value overrides the default

- WHEN a generation request supplies `negative_prompt="my custom negative"`
- THEN the job params SHALL carry `"my custom negative"` and SHALL NOT be
  replaced by the curated default

#### Scenario: Schema shape is unchanged

- WHEN the OpenAPI contract is regenerated from code
- THEN `negative_prompt` SHALL remain an optional string and the request/response
  shapes SHALL be otherwise unchanged (`tests/test_openapi.py` passes)

### Requirement: Serialized-JSON-string transport

The curated structured negative prompt SHALL reach the engine as a serialized
JSON string carried by the existing `negative_prompt` string field (the loader
returns the file's verbatim JSON text). The transport decision SHALL be recorded
in `docs/evidence_map.md`.

#### Scenario: Verbatim JSON text is transported

- WHEN the curated file is loaded and applied as the default
- THEN the value passed to the engine SHALL be the file's verbatim JSON text
  (a serialized string), not a flattened prose paragraph and not a changed field
  type

### Requirement: Graceful degradation on unavailable file

If the negative-prompt file is missing, unreadable, or not valid JSON, the API
SHALL log once at WARNING level and proceed with no negative prompt. Generation
SHALL NOT crash on account of an unavailable curated file.

#### Scenario: Missing file degrades gracefully

- WHEN the request omits `negative_prompt` and the curated file does not exist
- THEN the job SHALL proceed with no `negative_prompt` and a single WARNING log
  SHALL be emitted (no exception, no 5xx)

#### Scenario: Malformed file degrades gracefully

- WHEN the curated file exists but is not valid JSON
- THEN the loader SHALL return no default (`None`) and log once; generation
  SHALL proceed with no negative prompt

### Requirement: The file read is cached

The loader SHALL read the curated file at most once per process (cached), so the
per-request path does not re-read a ~15 KB file on every generation.

#### Scenario: Repeated loads read the file once

- WHEN the default negative prompt is requested multiple times within a process
- THEN the underlying file SHALL be read at most once (subsequent calls return
  the cached value)
