# AM-S6 Adversarial Verification — GATE-AM-S6-DOCS

Role: fresh-context adversarial verifier (did NOT write the docs, did NOT review them).
Date: 2026-07-26 · Task: falsify the done condition, find the surviving over-claim / lost caveat.

**VERDICT: FAIL.**

The README, the walkthrough, `docs/model_setup.md`, and the `docs/evidence_map.md`
audit all mark the three **video** generation modes — `t2v` (text→video), `i2v`
(image→video), and `t2v_audio` (video+audio) — as **"GPU-verified" on BOTH FP8 and
NVFP4**. There is **no recorded end-to-end GPU run** for any of these modes anywhere
in the evidence base, so the "GPU-verified" set in the README is **NOT a subset** of
what has a recorded run + owner PASS. This breaches **INV-6**, **R-13**, and the
session contract's own out-of-scope rule (a docs session may **report** AM-S2..S5
outcomes, it may **not create** a new per-mode result). The gate does not pass.

---

## 1. Disproven claims (contradicted by the recorded evidence)

### 1.1 (STRONGEST) "Video modes are GPU-verified on both FP8 and NVFP4" — NO recorded run exists (INV-6)

INV-6 (project_contract §3) is explicit and two-pronged: a mode is "GPU-verified"
only after **(i) a recorded end-to-end run on the RTX 5090** *and* **(ii) the owner's
recorded manual quality PASS — per format, per mode. Neither alone suffices.**

The README now asserts (README.md:116, 208; walkthrough.md:57–59; model_setup.md §6;
evidence_map.md AM-S6 audit) that `t2v`/`i2v`/`t2v_audio` are GPU-verified on **both**
formats. Checking prong (i) against every recorded GPU run in the repo:

| Recorded GPU-run evidence file | Modes with a recorded run |
|---|---|
| `docs/session_3/evidence/P2-action-e2e-and-t2i-nonregress-gpu.md` (FP8) | `t2i`, action (FD/policy/ID) |
| `docs/session_3/evidence/P1-action-omni-video-api-gpu.md` (FP8) | action (FD/policy/ID) |
| `docs/session_5/evidence/P1-t2i-action-nvfp4-gpu.md` (NVFP4) | `t2i`, action (FD/policy/ID) |
| `docs/session_5/evidence/P2-reasoner-nvfp4-w4a16-text-serve-PASS.md` (NVFP4) | reasoning |
| `docs/session_2/evidence/P2-fork-w8a16-text-serve-PASS.md` (FP8) | reasoning |
| `docs/session_4/evidence/P1-allmodes-smoke-gpu.md` (FP8) | t2i / reasoning / action |

**None of the recorded runs is a `t2v`, `i2v`, or `t2v_audio` generation.** The AM-S5
handoff matrix (`docs/handoff.md:33–37`) — the authoritative prior deliverable —
represents Studio by **`t2i` only**; there is no video row and no
`OWNER-AM-VIDEO-QUALITY` gate. The pre-AM-S6 `docs/model_setup.md` said in as many
words that the video modes were **"GPU-unverified (`S8`)"**, that only a
**"best-effort NVFP4 `t2v` smoke"** ran, and that **"`t2v_audio`/`i2v` and any full
validation of `t2v` remain unrun."** So `i2v` and `t2v_audio` had **never executed on
a GPU at all** before this docs-only session.

The session's own design doc concedes prong (i) is missing. `docs/session_6/design.md`
D2 (lines 28–30):

> "INV-6 needs (i) a recorded run + (ii) owner quality PASS. The owner supplied (ii)
> verbally and **attests (i) on their hardware**; captured as a dated attestation +
> amendment to the AM-S5 smoke-only matrix."

An owner's *verbal recollection* that "I ran it on my hardware" is not "a **recorded**
end-to-end run." If a verbal attestation could satisfy prong (i), the "recorded run"
requirement would be meaningless — and INV-6 pointedly says **neither prong alone
suffices**. The owner (PRD Decision 6) is the authority for prong (ii) *quality*, but
that authority cannot manufacture the *recorded run* that prong (i) demands, and it
certainly cannot conjure one for `i2v`/`t2v_audio`, which the repo's own record says
never ran.

The AM-S5 owner statement the "amendment" leans on is scoped, in the source, to two
named gates only: `OWNER-AM-REASON-QUALITY` and `OWNER-AM-ACTION-QUALITY`
(`docs/eval_seed_cases.md:239–241`; `docs/handoff.md:27–28`). "Checked every WebUI
tab, all functions work" is a *functional smoke* of the Studio tab, not a recorded,
per-video-mode quality verdict — and it produced no recorded video artifact.

**Net:** the README "GPU-verified" set (t2i + **t2v + i2v + t2v_audio** + reasoning +
action, ×2 formats) is a **superset** of the recorded+owner-PASSed set (t2i +
reasoning + action, ×2 formats). Done condition "the README verified set is a subset
of what passed the owner gate" is **false**.

### 1.2 Walkthrough "Expected output" for video modes that never ran (R-13)

R-13 / contract INV: "expected-output prose matches real owner-approved runs, never a
pre-run guess." `docs/walkthrough.md:57–59`:

> "**Expected:** a ~1280×720 clip (about 49 frames) that follows the prompt;
> **video+audio** adds a matching soundtrack. All three video modes are GPU-verified
> on both FP8 and NVFP4 with the owner's quality PASS (2026-07-26)."

The dimensions/frame-count are merely the documented config defaults (720p / 49
frames), so those numbers are not themselves fabricated — but the sentence presents a
video **result** as an observed, owner-approved run and stamps it "GPU-verified … with
the owner's quality PASS." No such run is recorded (see 1.1). This is precisely the
R-13 breach the contract's adversarial case #3 names.

Contrast — and this sharpens the finding — **every other** expected-output line in the
walkthrough traces cleanly to a recorded run:
- Reasoning `Red, Blue, Yellow` → `docs/session_2/evidence/P2-...:37`; the friction/gripper quote → `docs/session_4/evidence/P1-...:29`.
- Action FD "~0.6 MB, 17 frames" → `docs/session_3/evidence/P2-...:17` (614 KB, `num_frames=17`).
- Action policy `[16,29]` → session_3/P2:19 + session_5/P1:29; ID `[60,9]` → session_3/P2:18 + session_5/P1:30.
- `t2i` 480×480 PNG → session_3/P2 + session_5/P1.

The author was rigorous everywhere a recorded run existed and fabricated only where one
did not. That isolates the defect to the video block rather than sloppiness throughout.

### 1.3 A docs-only session created a verification result it was forbidden to create

`docs/session_6_contract.yaml` out_of_scope (line 21): *"Changing any verified behavior
or per-mode result — this session **reports** AM-S2..AM-S5 outcomes, it **does not
create them**."* Promoting `t2v`/`i2v`/`t2v_audio` × {FP8, NVFP4} from the AM-S5
recorded status **"smoke-only / unrun"** to **"GPU-verified · owner PASS"** on the
strength of a verbal attestation gathered *during this docs session*
(`docs/session_6/brainstorming.md:38–47`) is creating a per-mode result, not reporting
one. The label "owner-authorized amendment" does not change what it is.

### 1.4 Honest caveats were deleted, not just softened (INV-7 / honesty regression)

The prior docs carried an explicit, correct caveat that the two edited files **removed**:
- README (removed `-` line in the diff): *"A recommended 720p text→video smoke passed on both FP8 and NVFP4, but does not by itself promote the video, reasoning, or action modes to 'verified'."*
- `docs/model_setup.md` §6 (removed): *"A best-effort NVFP4 `t2v` smoke passed under `GPU-S3` … but `t2v_audio`/`i2v` and any full validation of `t2v` remain unrun; this residual limit is otherwise unchanged."*

Deleting the "smoke ≠ verified" caveat while flipping the status to "verified" is the
exact honesty-regression pattern the contract's adversarial case #6 and R-06 warn
about. (Note: this is the correct move *iff* the modes are genuinely verified; because
they are not per 1.1, removing the caveat compounds the over-claim.)

---

## 2. Unsupported / borderline claims

- **evidence_map.md AM-S6 audit — "the owner … attested that text→video, image→video,
  and video+audio were run on both FP8 and NVFP4 and judged high quality … this is an
  owner quality PASS."** The only place this attestation is recorded is inside AM-S6's
  own docs (evidence_map audit + `brainstorming.md`); it cites itself. There is no
  independent artifact, no evidence/Pn file, no GPU trace. Prong (ii) may be the
  owner's to give, but it is recorded here only as hearsay inside the session that
  benefits from it, and prong (i) is absent entirely.

- **walkthrough.md:7–9 header** — "Every mode here is GPU-verified on both FP8 and
  NVFP4 … the expected outputs are written against those real runs … not guessed."
  True for reasoning/action/t2i; **false for the three video modes** (no real run).

## 3. Checks that PASS (adversarial cases that did NOT fire — reported for completeness)

- **INV-1 (no committed image binary): PASS.** `git status --porcelain docs/images`
  is empty; `docs/images/` does not exist; the walkthrough carries 8 markdown
  placeholders, all under `docs/images/…` (walkthrough.md:47,61,62,63,88,116,122,126).
- **R-09 (BF16-base license reconciled, single & consistent): PASS.** README (173–176)
  and `docs/model_setup.md` (§1 note ¹, §2) both state base = **OpenMDW 1.1**,
  quantized `wfen/*` = **OpenMDW 1.0**, consistently. Independently verified against
  the contract's designated tie-breaker, the HF model card
  `https://huggingface.co/nvidia/Cosmos3-Nano`: `license: other` +
  `license_name: openmdw1.1-license` + `license_link: https://openmdw.ai/license/1-1/`
  → OpenMDW 1.1. The docs' explanation of *why* the HF tag reads `other` is correct.
- **Security caveats preserved: PASS.** README Status & security (216–227) keeps
  no-auth, loopback-by-default, root-equivalent Docker socket, and guardrails-off-by-
  design; walkthrough (13–15) repeats no-login / loopback / guardrails-off. None
  dropped or softened (adversarial case #6 does not fire on the *security* caveats).
- **Link resolver: PASS + negative control genuine.**
  `uv run python docs/session_6/check_links.py` → exit 0 ("all relative links and
  anchors resolve"). `--selftest` → exit 0 and **actually catches** a deliberately
  broken anchor (`bad.md:3: broken anchor '#does-not-exist'`); the resolver is not a
  no-op.
- **Blast radius: PASS.** `git status --short` shows only README.md,
  docs/evidence_map.md, docs/model_setup.md, docs/walkthrough.md, docs/session_6/** —
  all within the AM-S6 allowed set. (Note: `docs/risk_register.md`,
  `docs/eval_seed_cases.md`, `docs/handoff.md` are in the allowed set but were **not**
  modified in this working tree, though the audit/plan imply handoff/eval edits; not a
  gate breach, a minor incompleteness.)
- **NVFP4 limitation omission (case #2): does not fire** as an *omission* — every mode
  is (over-)claimed to pass on NVFP4. The defect is over-claim (case #1/#3), not a
  hidden NVFP4 limitation.

---

## 4. Strongest counterexample (single sentence)

`README.md:116` marks `POST /v1/generation/{t2v,i2v,t2v_audio}` **"GPU-verified"** on
both FP8 and NVFP4, yet **no `t2v`/`i2v`/`t2v_audio` generation has a recorded GPU run
in any `docs/session_*/evidence/` file** — `i2v` and `t2v_audio` were documented
"unrun" as recently as the pre-AM-S6 `docs/model_setup.md`, and the session's own
`design.md` D2 admits the owner only "attests (i) on their hardware" rather than
supplying the recorded run INV-6 requires.

## 5. Verdict & reasoning

**FAIL.** GATE-AM-S6-DOCS requires the README "GPU-verified" set to be a subset of what
passed the owner gate (INV-6), expected outputs to match real recorded runs (R-13), and
the honesty pass to find **no surviving over-claim**. A surviving over-claim exists and
is load-bearing: three of the four Studio generation modes are promoted to "GPU-verified
on both formats" with zero recorded GPU runs, on the basis of a verbal attestation
gathered inside this docs-only session — which the session was explicitly scoped **not**
to create. The BF16-license reconciliation, INV-1 placeholders, preserved security
caveats, and the link resolver (with a real negative control) all pass; the video-mode
over-claim alone fails the gate.

### Minimal path to PASS (for the owner/implementer, not applied here)
Either (a) scope the "GPU-verified" claim to what is recorded — Studio **`t2i`**,
Reasoning, Action on both formats — and restore the "video smoke ≠ verified" caveat for
`t2v`/`i2v`/`t2v_audio` (mark them Implemented · CPU-tested · smoke-only, or
owner-attested-pending-recorded-run); **or** (b) file and land an actual recorded
end-to-end GPU run for each of `t2v`/`i2v`/`t2v_audio` on each format (a `docs/session_6`
evidence/Pn artifact with the produced clip's bytes/dimensions, mirroring the t2i/action
evidence) plus the owner's recorded per-mode quality verdict, then the current wording
becomes truthful.

---

# Re-verification (post-fix) — 2026-07-26

**Re-VERDICT: PASS.**

The FAIL above was escalated, not overridden — I confirmed the process and the fix by
reading the changed files fresh. Path (b) from my "minimal path to PASS" was taken. The
surviving over-claim I named is **cured**, and no new over-claim or lost caveat was
introduced. Reasoning, with the skeptical checks I ran:

### What changed (verified present, not just asserted)
1. **Finding formally classified + escalated.** `docs/session_6/failure_arbiter.md`
   exists and classifies my finding as **AMBIGUITY (bordering SPEC_GAP)** over whether an
   owner-operated run satisfies INV-6 limb (i). It states both readings faithfully (mine
   is "Reading A"), and — critically — it labels **both** unilateral moves *forbidden*:
   silently keeping "GPU-verified" on the disputed reading, **and** silently downgrading
   against the owner's instruction. It routes to a mandatory owner decision. This is the
   correct STOP-and-escalate behavior; my FAIL was taken seriously.
2. **Owner (the PRD-Decision-6 authority) ruled:** record the runs, keep "GPU-verified".
3. **A recorded run artifact now exists:** `docs/session_6/evidence/P1-owner-video-runs.md`
   records owner-operated end-to-end runs of `t2v`/`i2v`/`t2v_audio` on **both** FP8 and
   NVFP4 via the WebUI Studio — valid ~1280×720 (~49-frame) clips produced and played
   back, **audio present** for `t2v_audio`, judged high quality. It maps INV-6 (i)+(ii)
   explicitly.
4. **Citations updated:** `docs/model_setup.md` §6 and the `docs/evidence_map.md` AM-S6
   audit now cite P1 and state both limbs.

### Why this now satisfies the gate's standard ("no HIDDEN / MISREPRESENTED / UNAUTHORIZED / softened claim")
- **INV-6 limb (i) is now on record — and INV-6 does not require the record to be
  agent-captured.** INV-6's text is "a recorded end-to-end run on the RTX 5090." The
  t2i/reasoning/action P-files are *instrumented* runs, which is a **stronger** form of
  evidence, not the definitional minimum. A dated, recorded, owner-operated run by the
  quality-gate authority meets the literal requirement. Both limbs are cited.
- **The weaker evidence tier is DISCLOSED, not dressed up as a probe — this is decisive.**
  `P1-owner-video-runs.md` (lines 34–38) states in as many words that it is **owner-
  operated** and **"not an agent-captured GPU probe with byte-level artifact metadata (as
  the t2i/reasoning/action P-files are) … no synthetic detail is added."** The
  `evidence_map.md` audit repeats the same disclosure. Skeptical check for fabrication:
  P1 invents **no** file sizes, magic bytes, or VRAM traces (the exact fiction my original
  FAIL guarded against); the only specifics are the shipped config defaults (1280×720 /
  49 frames) plus one observable fact (audio present). Nothing is misrepresented — a
  reader is told precisely what tier of evidence backs the video claim and can weigh it.
- **Authorized + scoped.** The authority (owner) made the call; scope is strictly
  `t2v`/`i2v`/`t2v_audio` × {FP8, NVFP4}; P1 and the audit both state nothing else in the
  matrix was re-touched, and `t2i`/reasoning/action retain their own AM-S2..S5 evidence
  (I re-checked: those citations are unchanged and still traceable).
- **R-13 cured.** `docs/walkthrough.md:57–59` ("GPU-verified on both FP8 and NVFP4 with
  the owner's quality PASS (2026-07-26)") and the header (7–9, "written against those real
  runs, not guessed") now trace to a real recorded run (P1) via the evidence map. The
  expected-output prose matches what P1 records the owner observed.
- **No lost caveat.** The removed "720p smoke ≠ verified" caveat is now *correctly
  obsolete* — the modes are verified (both limbs recorded). Keeping a caveat that has
  become false would itself be dishonest; removing it is not a "lost caveat."

### Everything else re-confirmed still green
- **Links:** `check_links.py` exits 0; `--selftest` genuinely catches a broken anchor
  (negative control real, not a no-op).
- **INV-1:** `git status --porcelain docs/images` empty; no image binary (the new P1 is a
  markdown file under `docs/session_6/evidence/`, an allowed path).
- **R-09 license:** README ↔ `model_setup.md` still consistent (base OpenMDW 1.1 /
  quantized OpenMDW 1.0), unchanged by the fix; still matches the HF model card.
- **Security caveats:** no-auth / loopback / root-Docker-socket / guardrails-off /
  one-stack-at-a-time all still present — untouched by the fix.
- **Blast radius:** `git status --short` = README.md, docs/evidence_map.md,
  docs/model_setup.md, docs/walkthrough.md, docs/session_6/** — all within the AM-S6
  allowed set (the new `docs/session_6/evidence/` + `failure_arbiter.md` are inside
  `docs/session_6/**`).

### Residual (named, but NOT gate-failing)
The video modes rest on a **self-reported** run by the owner, a weaker evidence tier than
the instrumented probes backing t2i/reasoning/action. This is a real asymmetry — but it
is **disclosed three times** (P1, evidence_map, model_setup), **authorized** by the
quality-gate authority, and **scoped**. Disclosed weaker-but-authorized evidence is not
an over-claim; it would only breach the gate if the docs presented it as equivalent to
the instrumented runs, and they explicitly do the opposite. If the owner later wants
parity, an agent-captured video probe (clip bytes/container/dimensions, like P2 for
action) would upgrade the tier — a hardening nicety, not a gate requirement.

**Bottom line:** GATE-AM-S6-DOCS's done condition — README "See it in action" links the
walkthrough; per-mode example input → expected output with `docs/images/` placeholders
and no committed binary; the README verified set is a subset of the owner-passed set; the
BF16 license reconciled; every internal link resolves; and **no surviving over-claim or
lost caveat** — is now met. **PASS.**
