# Capability: media-viewport

Status: MODIFIED (UX-S3)
Refs: FR-8; `EV-UX-MEDIA-ENLARGED`; E-11; contract invariant "enlargement stays
responsive on small screens".

The generated-media viewport is enlarged so the media is the centerpiece of the
Studio, while remaining responsive and keeping the Review compare-grid intact.

## MODIFIED Requirements

### Requirement: Enlarged media bounds

The `MediaPreview` media element `max-height` SHALL be greater than the `60vh`
baseline (set to `80vh`), and the Studio container `max-width` SHALL be greater
than the `60rem` baseline (set to `80rem`, ≈ the native 1280px width of the
default 720p video). Neither the old `60vh` media cap nor the old `60rem`
container cap SHALL remain.

#### Scenario: Media max-height is raised above the baseline

- WHEN `webui/components/MediaPreview.module.css` is inspected
- THEN `.media` `max-height` SHALL be `80vh`
- AND it SHALL NOT contain `max-height: 60vh`

#### Scenario: Studio container max-width is raised above the baseline

- WHEN `webui/app/(studio)/studio/page.module.css` is inspected
- THEN `.studio` `max-width` SHALL be `80rem`
- AND it SHALL NOT contain `max-width: 60rem`

### Requirement: Enlargement remains responsive

The enlarged bounds SHALL be expressed as caps (`max-height` in `vh`,
`max-width` in `rem`) and the media element SHALL retain `max-width: 100%`, so
that on any viewport narrower than the container the media shrinks to fit its
column rather than overflowing. No fixed pixel `height`/`width` SHALL be
introduced on the media element.

#### Scenario: Media still fits narrow columns

- WHEN `.media` is inspected
- THEN it SHALL retain `max-width: 100%`
- AND it SHALL NOT declare a fixed pixel `height` or `width`

#### Scenario: Enlarged media renders within a narrow viewport without overflow

- WHEN the Review result is displayed in a narrow viewport (e.g. 375px wide)
- THEN the rendered media element's width SHALL NOT exceed the viewport width

### Requirement: Review compare-grid intact

The Review compare-grid SHALL remain a two-column layout
(`grid-template-columns: 1fr 1fr`) so that a current result and a selected
comparison render side by side, each media constrained to its half-column.

#### Scenario: Compare view renders two media side by side

- WHEN a comparison job is selected in the Review panel
- THEN the current and comparison media SHALL render in a two-column grid, each
  constrained to `max-width: 100%` of its column
