# Spec — `docs-links-and-license`

Capability: internal-link/anchor integrity across the edited docs **and** the single, consistent
BF16-base license statement (E-14). Backed by `EV-AM-DOCS-LINKS-RESOLVE` (R-09).

## ADDED Requirements

### Requirement: Every internal link and anchor resolves
Every relative link and in-page anchor in `README.md`, `docs/walkthrough.md`, and `docs/model_setup.md`
SHALL resolve — relative file links to an existing path, and `#anchor` fragments to a heading that
GitHub's slug algorithm would produce in the target document.

#### Scenario: All internal links resolve
- WHEN the relative-link + anchor resolver runs over README.md, docs/walkthrough.md, docs/model_setup.md
- THEN every relative file link points to an existing file and every `#fragment` matches a real heading
  slug in its target document; the resolver exits 0.

#### Scenario: Broken link is caught (negative control)
- WHEN a deliberately broken link (e.g. `](#does-not-exist)`) is fed to the resolver
- THEN the resolver reports it and exits non-zero (proving the check is not a no-op).

## MODIFIED Requirements

### Requirement: BF16-base license stated once, consistently (E-14 → OpenMDW 1.1)
The BF16 base `nvidia/Cosmos3-Nano` license SHALL be stated as **OpenMDW 1.1** — reconciled against the
authoritative Hugging Face source (`license: other` + `license_name: openmdw1.1-license` +
`license_link: https://openmdw.ai/license/1-1/`) — once and consistently across `docs/model_setup.md`
and `README.md`. The quantized `wfen/*` checkpoints SHALL remain **OpenMDW 1.0**. No document SHALL carry
the pre-reconciliation contradiction (bare `other` vs the owner's `openmdw-1.0`).

Full updated content:
- `docs/model_setup.md` §1 checkpoint table: base license cell = `OpenMDW 1.1` (with a one-line note that
  the HF `license:` tag is `other` because OpenMDW is not in HF's SPDX list; `license_name:
  openmdw1.1-license`, link `https://openmdw.ai/license/1-1/`).
- `docs/model_setup.md` §2 Licensing: state code = MIT; quantized weights = OpenMDW 1.0; base = OpenMDW
  1.1; keep the "distinct from the repo's MIT license; do not describe weights as MIT" rule (INV-7).
- `README.md` Licensing note + Checkpoint-setup: quantized weights OpenMDW 1.0; the legacy base OpenMDW
  1.1; no bare-`other` base claim remains.

#### Scenario: Base license is OpenMDW 1.1 everywhere it appears
- WHEN `rg -n "nvidia/Cosmos3-Nano|OpenMDW|openmdw|\bother\b" README.md docs/model_setup.md` runs
- THEN the base license is stated as OpenMDW 1.1 (never as a bare `other` license claim and never as
  `openmdw-1.0`), and the quantized checkpoints remain OpenMDW 1.0 — consistent across both files.

#### Scenario: Weights are never described as MIT (INV-7)
- WHEN the licensing prose in README.md and docs/model_setup.md is read
- THEN repo code is MIT and model weights carry their own OpenMDW licenses, stated separately; no line
  describes the weights as MIT.
