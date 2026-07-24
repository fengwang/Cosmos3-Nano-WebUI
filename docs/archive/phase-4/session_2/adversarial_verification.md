# LX-S2 Adversarial Verification — README Honesty Pass

Date: 2026-07-24
Verifier: fresh-context adversarial agent per
`docs/agent_workflow/prompts/adversarial_verifier.md`. It did not write the
README and did not see the implementation conversation; it saw only the session
contract, the project contract, the `git diff`, and the check evidence, and was
told to assume the completion claim is false. This is the **mandatory**
no-over-claim / no-lost-caveat pass required by the routing (`R-04`), run despite
the low risk level.

## Verdict: **PASS**

Single most important reason: the diff is a pure documentation restructure that
**adds** orientation (hook, ordered runnable TL;DR, a faithful 5-node Mermaid map,
`<details>`, in-page nav) while keeping the honest Status & security section
**fully visible at the end as a strict superset** of the prior one — including the
new, accurately-stated 30-min idle keep-warm — with only text→image claimed
GPU-verified, every link resolving, and no cloud CTA. No caveat was lost, hidden,
or softened, and no new over-claim was introduced.

## Attack results (every contract adversarial case)

| # | Adversarial case | Result | Evidence |
|---|---|---|---|
| 1 | Punchy hook implies every mode is production-ready / verified | **Failed to falsify** | Hook is literally true; the immediately-following `> [!NOTE]` states "today **only text→image** is GPU-verified end to end; the other modes are implemented and CPU-tested". Per-mode status preserved. |
| 2 | A caveat dropped / softened / hidden in `<details>` | **Failed to falsify** | Diffed `git show HEAD:README.md` (old) vs new: new Status & security is visible (not collapsed) and a **strict superset** — five posture facts at full strength + a new keep-warm bullet. Consistent with `SECURITY.md`. |
| 3 | Cloud / Codespaces CTA present | **Failed to falsify** | `rg` sweep zero matches; checker P5-no-cloud-cta = none. |
| 4 | TL;DR drops / reorders a required step | **Failed to falsify** | Order intact: clone → pinned `hf download` (`9bf5d6ae1646…`, matches `model_setup.md`) → `make build` → `make up-fp8` → `make health` → open Studio; all `make` targets exist. |
| 5 | Broken `<details>` (no blank line) or essentials only inside a `<details>` | **Failed to falsify** | Both `<details>` have the blank line after `</summary>`; they hold only optional NVFP4/reasoning + troubleshooting. Primary quickstart and all caveats are outside any `<details>`. |
| 6 | An unsupported "why"/benefit claim | **Failed to falsify** | Keep-warm→no-cold-reload → E-02; "different model still preempts immediately" → E-05 + `manager.py` acquire; "prefer NVFP4 for headroom" → compose comment + E-20. |
| 7 | Mermaid >7 nodes or wrong flow | **Failed to falsify** | 5 nodes; flow matches `webui/app/api/[...path]/route.ts` (server-side proxy), `manager.py`/`container.py` (socket lifecycle), `docker-compose.base.yml` (docker.sock + GPU container). |
| 8 | A dangling internal link/anchor | **Failed to falsify** | All 34 targets resolve; every `#anchor` maps to a real heading slug. |
| 9 | Per-mode wording drifted ahead of the evidence map | **Failed to falsify** | README never labels t2v/i2v/reasoning/action "verified"; explicitly says the smoke "does not by itself promote those modes to 'verified'". |
| 10 | 30-min idle statement inaccurate | **Failed to falsify** | `api/app/main.py` default `"1800"`; `manager.py` `idle_timeout=1800.0`; `0` disables; mechanics match `notify_idle`/`_on_idle_timeout`/`_try_idle_evict`. |

## Strongest counterexample found (does not falsify)

README says the 720p t2v smoke "passed on **both FP8 and NVFP4**," while the
current-phase `docs/model_setup.md` mentions only a best-effort **NVFP4** t2v
smoke. This does not falsify the gate: the wording is **verbatim pre-existing**
in the HEAD README (LX-S2 only re-wrapped it), it is not a "verified" claim, the
"both FP8/NVFP4" 720p-fit smoke is backed by the phase-3 archive
(`docs/archive/phase-3/**`, E-17/E-18), and `docs/model_setup.md` is outside
LX-S2's blast radius. Recorded as a residual doc-consistency note (handoff), not
a surviving over-claim introduced by this session.

## Deterministic checker

16/16 pass. The verifier independently confirmed the checker's logic (GitHub slug
algorithm, code-fence stripping, arrow normalization, wrap-robust t2i-subject
context window) and reasoned from source rather than trusting the pass.
