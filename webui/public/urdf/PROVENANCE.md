# URDF Asset Provenance — Session 10 Action Viewer

## Asset
- **File:** `agibotworld.urdf`
- **Origin:** **Authored in-repo** for this project (Session 10). It is **not** a vendored or downloaded
  third-party robot model.
- **License:** the repository's license (same as the rest of `cosmos3-nano-webui`). No third-party asset
  license applies because no third-party asset is used.
- **External dependencies:** **none.** The URDF uses only primitive geometry (`<box>`, `<cylinder>`,
  `<sphere>`) — there are **no external mesh files** (no `.stl` / `.dae` / `.obj`) and **no remote URLs**.
  It is therefore loaded same-origin and fully offline (INV-1; the "URDF/mesh from an untrusted remote URL"
  security adversarial case is structurally excluded).

## Embodiment
- **Domain:** `agibotworld` — one of the two S4-verified action embodiments (FD/policy, 29-D). It is the
  single embodiment given the 3D path in Session 10; `av` (9-D autonomous vehicle) is 2D-plot only.
- **Actuated dimensions:** **29**, matching the canonical action width in
  `api/preprocessing/action_schema.py` (`_RAW_ACTION_DIM["agibotworld"] == 29`). The viewer asserts this
  equality at load (`validateJointMap`); a mismatch refuses the 3D render (INV-6 / RK-12).

## ⚠️ Joint-map is a CANDIDATE CONVENTION, not ground truth (RK-04)
The action engine's **true per-dimension → joint semantic layout for `agibotworld` is undocumented** in this
repository and the engine tables (`action_schema.py` records only the *width*, 29, not the per-dim meaning).
The dim→joint mapping declared in `webui/components/action-viewer/jointmap.ts` and realized by this URDF is
therefore a **declared candidate convention**, authored for visualization. It is:
- **structurally validated** (29 dims, contiguous coverage, every joint exists in this URDF), and
- **gated by the human visual gate** (EC-U3) for motion/axis correctness,
but it is **NOT asserted to be the engine's authoritative semantic layout**. The **2D trajectory plot is the
always-correct floor** (it makes no semantic claim). A confirmed layout is a tracked follow-up (eval seed).
