# GPU-S2 Implementation Plan

Input: `docs/session_2/tasks.md`, `docs/session_2/design.md`,
`docs/session_2/specs/*.md`. Two target repos are **external** to this git
repository — every command below states which repo it targets. `$SCRATCH`
denotes the session scratchpad directory (never
`/data/models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise*`).

## Step 1 (Task 1.1-1.2) — Baseline, no commit anywhere

```bash
command -v git-lfs && command -v hf && hf auth whoami
curl -sI --max-time 6 https://huggingface.co | head -1
mkdir -p "$SCRATCH/baseline" && cd "$SCRATCH/baseline"
export GIT_LFS_SKIP_SMUDGE=1 HF_HOME="$SCRATCH/baseline/.hf-cache"
git clone https://huggingface.co/wfen/Cosmos3-Nano-FP8-Blockwise fp8-baseline
git clone https://huggingface.co/wfen/Cosmos3-Nano-NVFP4-Blockwise nvfp4-baseline
ls fp8-baseline/model.safetensors.index.json nvfp4-baseline/model.safetensors.index.json
git -C fp8-baseline log --oneline -1   # expect 4e181f9…
git -C nvfp4-baseline log --oneline -1 # expect b5c9332…
```

**Check:** both stale index files are present at the documented pre-fix
revisions, from a client that has never cached these repos before — this is
the "before" evidence baseline. No commit (read-only against the external
repos, nothing written to this repository).

## Step 2 (Task 2.1-2.5) — FP8 fix, local (target: `wfen/Cosmos3-Nano-FP8-Blockwise`)

```bash
mkdir -p "$SCRATCH" && cd "$SCRATCH"
git clone -c "lfs.fetchexclude=*.safetensors,*.pt,*.mp4,*.png,*.jpg,*.jpeg" \
  https://huggingface.co/wfen/Cosmos3-Nano-FP8-Blockwise fp8-fix
cd fp8-fix
git log --oneline -1   # confirm HEAD == 4e181f996abf03f3425298ef692e6e5e56fd46a4
```

(Amended, GPU-S2-A1: **not** `GIT_LFS_SKIP_SMUDGE=1` — that leaves every
small file unsmudged too, which would corrupt them at the renormalize step
below. The targeted `lfs.fetchexclude` only skips the genuinely large/binary
patterns; every small file smudges normally.)

**Commit 1 — remove the stale index and restore the orphaned compliance docs:**

```bash
git rm model.safetensors.index.json

# GPU-S2-A1: BIAS.md/EXPLAINABILITY.md/PRIVACY.md/SAFETY.md check out as raw
# LFS-pointer text regardless of clone flags (no .gitattributes rule has ever
# matched .md). Fetch the real object and smudge it manually, bypassing the
# attribute-gated checkout path.
for f in BIAS.md EXPLAINABILITY.md PRIVACY.md SAFETY.md; do
  git lfs fetch --include="$f" origin
  git show HEAD:"$f" | git-lfs smudge -- "$f" > "$f.real"
  mv "$f.real" "$f"
done
wc -c BIAS.md EXPLAINABILITY.md PRIVACY.md SAFETY.md
# expect: 4720 BIAS.md, 3189 EXPLAINABILITY.md, 1215 PRIVACY.md, 3677 SAFETY.md
git add BIAS.md EXPLAINABILITY.md PRIVACY.md SAFETY.md
git commit -m "Remove stale top-level weight index; restore orphaned compliance docs

model.safetensors.index.json referenced 7 non-existent
transformer/diffusion_pytorch_model-0000N-of-00007 shards; the real weight is
one consolidated transformer/diffusion_pytorch_model.safetensors.

BIAS.md/EXPLAINABILITY.md/PRIVACY.md/SAFETY.md were checking out as raw
LFS-pointer text (no .gitattributes rule has ever matched .md, so neither a
plain clone nor git-lfs's own tooling re-smudges them); restored their real
content from the underlying LFS objects."
```

**Edit `.gitattributes`** (`Edit` tool, this exact working copy): remove
these 5 lines, leave every other line (including
`text_tokenizer/tokenizer.json filter=lfs diff=lfs merge=lfs -text`,
`*.mp4`, `*.png`, `*.jpg`, and every binary pattern) untouched:

```
*.txt filter=lfs diff=lfs merge=lfs -text
*.csv filter=lfs diff=lfs merge=lfs -text
*.json filter=lfs diff=lfs merge=lfs -text
*.py filter=lfs diff=lfs merge=lfs -text
*.jinja filter=lfs diff=lfs merge=lfs -text
```

**Pre-renormalize orphan scan (GPU-S2-A1) — before Commit 2:**

```bash
for f in $(git lfs ls-files | awk '{print $3}'); do
  case "$f" in
    *.safetensors|*.pt|*.mp4|*.png|*.jpg|text_tokenizer/tokenizer.json) continue ;;
  esac
  head -c 8 "$f" | grep -q "^version " && echo "ORPHAN (unexpected): $f"
done
# expect exactly 3 lines: _s2_postfix.md, _s2_rerun.md, _s2_verify.md
# (known, intentionally left corrupted — Owner Decision 3). Any other name
# printed here is a newly-discovered orphan: stop and fetch+smudge it like
# the four compliance docs above before proceeding.
```

**Commit 2 — renormalize, with the R-04 guard before committing:**

```bash
git lfs ls-files | sort > /tmp/fp8-lfs-before.txt
git add --renormalize .
git lfs ls-files | sort > /tmp/fp8-lfs-after.txt

LARGE='transformer/(diffusion_pytorch_model|model)\.safetensors|vae/diffusion_pytorch_model\.safetensors|vision_encoder/model\.safetensors|sound_tokenizer/diffusion_pytorch_model\.safetensors|transformer/modelopt_state\.pt'
diff <(grep -E "$LARGE" /tmp/fp8-lfs-before.txt) <(grep -E "$LARGE" /tmp/fp8-lfs-after.txt)
# must print nothing — large weight OIDs unchanged (R-04 guard)
comm -13 /tmp/fp8-lfs-before.txt /tmp/fp8-lfs-after.txt
# must print nothing — no file newly entered LFS

git commit -m "Fix LFS tracking for small text files

Blanket *.json/*.py/*.txt/*.csv/*.jinja rules forced every small
config/tokenizer/script file into LFS regardless of size. Removed those
rules and renormalized; text_tokenizer/tokenizer.json (11.4 MB) keeps its
explicit size-justified LFS override. Large weight files are unaffected."
```

**Self-critique gate (Failure Arbiter before any fix if this repeats):** if
the large-file diff is non-empty, this is a BUG in the `.gitattributes` edit
(a pattern was mis-scoped) — fix the patterns and redo the renormalize, do
not push. If the "newly entered LFS" set is non-empty, same treatment.

**Local verification (Task 2.5):**

```bash
for f in config.json checkpoint.json chat_template.json load_quantized.py \
         BIAS.md EXPLAINABILITY.md PRIVACY.md SAFETY.md; do
  head -c 20 "$f"; echo   # must NOT start with "version https://git-lfs"
done
wc -c BIAS.md EXPLAINABILITY.md PRIVACY.md SAFETY.md   # 4720/3189/1215/3677
test ! -e model.safetensors.index.json && echo "no stale index: OK"
head -c 8 _s2_postfix.md   # expect "version " — deliberately still corrupted
```

## Step 3 (Task 2.6-2.8) — FP8 push gate, push, independent verify

**Stop.** Ask the owner explicitly: "push FP8 now?" — a standalone message,
never combined with any other action. Proceed only on an explicit yes.

```bash
git push   # only after the go-ahead above
```

Independent, cache-isolated fresh verify (separate `HF_HOME`, never reused
from Step 1/2):

```bash
mkdir -p "$SCRATCH/fp8-verify" && cd "$SCRATCH"
export GIT_LFS_SKIP_SMUDGE=1 HF_HOME="$SCRATCH/fp8-verify/.hf-cache"
git clone https://huggingface.co/wfen/Cosmos3-Nano-FP8-Blockwise fp8-verify
git -C fp8-verify log --oneline -1   # record as the new FP8 revision
hf download wfen/Cosmos3-Nano-FP8-Blockwise --revision "$(git -C fp8-verify rev-parse HEAD)" \
  --local-dir "$SCRATCH/fp8-verify-hf" \
  --exclude "*.safetensors" --exclude "*.pt"
head -c 20 "$SCRATCH/fp8-verify-hf/config.json"; echo   # must be real JSON, not a pointer
```

**Check (`GATE-GPU-S2-CHECKPOINT`, FP8 half):** new revision resolves via
both tools; `config.json` (and siblings) are real content; no stale index.
Record the new revision SHA — this becomes the FP8 pin for Step 6.

## Step 4 (Task 3.1-3.8) — NVFP4 fix, push gate, push, independent verify (target: `wfen/Cosmos3-Nano-NVFP4-Blockwise`)

Same shape as Steps 2-3, with the re-derived (not copied) recipe:

```bash
mkdir -p "$SCRATCH" && cd "$SCRATCH"
git clone -c "lfs.fetchexclude=*.safetensors,*.pt,*.mp4,*.png,*.jpg,*.jpeg" \
  https://huggingface.co/wfen/Cosmos3-Nano-NVFP4-Blockwise nvfp4-fix
cd nvfp4-fix
git log --oneline -1   # confirm HEAD == b5c9332efbaefa72c99890b1b1150da12ca9256c
cat .gitattributes   # re-confirm no blanket *.json/*.py/*.txt/*.jinja line exists
```

(Same amended clone mechanism as Step 2 — targeted exclude, not blanket
skip-smudge.)

**Commit 1 — remove the stale index and restore the orphaned compliance docs:**

```bash
git rm model.safetensors.index.json

for f in BIAS.md EXPLAINABILITY.md PRIVACY.md SAFETY.md; do
  git lfs fetch --include="$f" origin
  git show HEAD:"$f" | git-lfs smudge -- "$f" > "$f.real"
  mv "$f.real" "$f"
done
wc -c BIAS.md EXPLAINABILITY.md PRIVACY.md SAFETY.md
# expect the same 4720/3189/1215/3677 bytes as FP8 (shared boilerplate, same OIDs)
git add BIAS.md EXPLAINABILITY.md PRIVACY.md SAFETY.md
git commit -m "Remove stale top-level weight index; restore orphaned compliance docs

model.safetensors.index.json referenced 7 non-existent
transformer/model-0000N-of-00007 shards; the real weight is one consolidated
transformer/model.safetensors.

BIAS.md/EXPLAINABILITY.md/PRIVACY.md/SAFETY.md were checking out as raw
LFS-pointer text (same root cause and fix as the FP8 repo)."
```

**`.gitattributes`:** expected to need **no edit** (already scoped
correctly — confirmed during brainstorming). If the `cat` above shows a
blanket text-extension rule after all, re-derive the removal from NVFP4's
own current content rather than reusing FP8's diff, then proceed as below.

**Pre-renormalize orphan scan (GPU-S2-A1) — before Commit 2:**

```bash
for f in $(git lfs ls-files | awk '{print $3}'); do
  case "$f" in
    *.safetensors|*.pt|*.mp4|*.png|*.jpg|text_tokenizer/tokenizer.json) continue ;;
  esac
  head -c 8 "$f" | grep -q "^version " && echo "ORPHAN (unexpected): $f"
done
# expect zero lines — NVFP4 has no dev-scratch equivalent to _s2_*.md, so
# every orphan here should already be one of the four just restored above.
```

**Commit 2 — renormalize only (or renormalize + edit, if 3.3 found a gap), same R-04 guard:**

```bash
git lfs ls-files | sort > /tmp/nvfp4-lfs-before.txt
git add --renormalize .
git lfs ls-files | sort > /tmp/nvfp4-lfs-after.txt
LARGE='transformer/(diffusion_pytorch_model|model)\.safetensors|vae/diffusion_pytorch_model\.safetensors|vision_encoder/model\.safetensors|sound_tokenizer/diffusion_pytorch_model\.safetensors'
diff <(grep -E "$LARGE" /tmp/nvfp4-lfs-before.txt) <(grep -E "$LARGE" /tmp/nvfp4-lfs-after.txt)
comm -13 /tmp/nvfp4-lfs-before.txt /tmp/nvfp4-lfs-after.txt
git commit -m "Fix LFS tracking for small text files

Small config/provenance files were committed as LFS pointers before the
blanket text-extension rule was removed from .gitattributes and were never
renormalized. Large weight files are unaffected."
```

Local verification: same shape as Step 2's (2.5), minus the `_s2_*.md`
check, which doesn't apply here.

**Stop.** Ask the owner explicitly: "push NVFP4 now?" — independent of FP8's
go-ahead, standalone message.

```bash
git push   # only after that go-ahead
```

Independent fresh verify: same shape as Step 3's, against
`wfen/Cosmos3-Nano-NVFP4-Blockwise`. Record the new NVFP4 revision SHA.

## Step 5 (Task 4.1-4.3) — Verification probe (target: this repo, `docs/session_2/probes/`)

Write `docs/session_2/probes/verify_gpu_s2_checkpoints.py` — pure core
(classify a manifest entry as "small-plain-text-but-LFS", "large-but-not-LFS",
or "ok"; detect stale-index presence) separated from an `HfApi`-based shell
(`list_repo_files`, `get_paths_info`) plus a `--check` mode with no network.
First failing/self-test to write (TDD): the pure classifier against a
hand-built fixture manifest before it's ever pointed at the network.

```bash
python3 docs/session_2/probes/verify_gpu_s2_checkpoints.py --check
python3 docs/session_2/probes/verify_gpu_s2_checkpoints.py \
  --out docs/session_2/probes
```

**Commit point:** `feat(gpu-s2): checkpoint LFS/index verification probe`.

## Step 6 (Task 5.1-5.6) — Re-pin sweep (target: this repo)

Edit, in this order, using the two new revision SHAs recorded in Steps 3/4:

1. `docs/model_setup.md` §1 (table) and §8/§9 (drop the now-obsolete
   workaround instructions; the download example uses the new revision).
2. `docs/evidence_map.md` — new evidence rows (fix + fresh-clone/`hf
   download` results for both repos).
3. `docs/release_checklist.md` §7.
4. `docs/eval_seed_cases.md` — "Public Checkpoint IDs" (new revisions
   current; pre-fix SHAs kept only in the existing historical note).
5. `docs/risk_register.md` — R-02 (revision-change note), R-03 (sweep
   executed), R-04 (no large file de-LFS'd, evidenced by Steps 2/4's OID
   diffs).

```bash
rg -n --hidden --glob '!.git' "4e181f99|b5c9332e" .
```

(`--hidden` required — `rg` skips dotfiles by default; the un-hidden form
missed `.env.example`, caught only by adversarial verification and fixed as
amendment `GPU-S2-A3`.)

**Check:** the only matches are `docs/eval_seed_cases.md`'s own historical
note and this session's own planning/evidence prose. Any other match is a
hard stop — fix that file and re-run before proceeding.

**Commit point:** `docs(gpu-s2): re-pin sweep — model_setup/evidence_map/release_checklist/eval_seed_cases/risk_register`.

## Step 7 (Task 6) — Review and adversarial verification

Dispatch sharded review (5 axes: correctness, security, tests, architecture,
performance) and a fresh-context adversarial verifier once Steps 1-6 are
committed (brief in `docs/session_2/execution_contract.md`). Fix
High/Critical findings only, re-run the specific check each finding
affects, commit fixes separately: `fix(gpu-s2): address sharded-review
finding <id>`.

## Step 8 (Task 7) — Session close

Re-run the full deterministic check list from `session_2_contract.yaml` end
to end against the final committed state (both repos + this repo), verify
`GATE-GPU-S2-CHECKPOINT`'s done condition, write `docs/handoff.md` and
`docs/eval_seed_cases.md` seeds.

**Commit point:** `docs(gpu-s2): handoff + eval seeds`.
