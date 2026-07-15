# Capability: webui-declutter

Status: MODIFIED (UX-S3)
Refs: FR-7, INV-7; `EV-UX-GALLERY-GONE`; E-10.

The developer Component Gallery is removed from the WebUI, and the home route
lands users on the Generation Studio instead of a stale stub.

## REMOVED Requirements

### Requirement: Component Gallery route

The design-system Component Gallery route (`/gallery`) and its showcase page
SHALL be removed from the WebUI. After removal, no `/gallery` route resolves and
no code references `webui/app/gallery/**`.

**Reason:** The gallery is a developer/design-system test surface, not an
end-user capability; it was surfaced as a primary nav item and as the only
actionable content of the home page, which is friction for a task-first media
tool (PRD §1, §3.6; E-10).

**Migration:** No user-facing replacement. The gallery is imported by nothing,
so removal is a pure deletion; the design-system components it demonstrated
remain available to the application unchanged. Any future component reference
belongs in developer tooling, not a shipped route.

#### Scenario: The gallery route no longer exists

- WHEN the WebUI is built
- THEN no `/gallery` route SHALL be emitted, and the directory
  `webui/app/gallery/` SHALL NOT exist

#### Scenario: No code references the gallery

- WHEN `rg -i "gallery|/gallery"` is run over `webui/app` and `webui/components`
- THEN the only match SHALL be the unrelated `HistoryList` "History/gallery"
  documentation comment

## MODIFIED Requirements

### Requirement: Primary navigation items

The primary navigation rail SHALL list exactly `Studio`, `Reasoning`,
`Action`, and `History`, and SHALL NOT list a `Gallery` item. The active-item
highlight behavior (exact match or path-prefix match) SHALL be unchanged.

#### Scenario: Nav rail omits Gallery

- WHEN the primary navigation renders
- THEN it SHALL render links to `/studio`, `/chat`, `/action`, and `/history`
- AND it SHALL NOT render any link whose target is `/gallery` or whose label is
  `Gallery`

### Requirement: Home route lands on the Studio

The home route `/` SHALL take the user to the Generation Studio rather than
rendering a static stub. It SHALL do so by redirecting to `/studio`, leaving no
dead link on the home route.

#### Scenario: Visiting the home route redirects to the Studio

- WHEN a request is made to `/`
- THEN the response SHALL redirect to `/studio`

#### Scenario: The home route contains no dead gallery link

- WHEN the home route module is rendered
- THEN it SHALL NOT contain a link to `/gallery` (nor any other dead link); its
  effect SHALL be solely the redirect to `/studio`
