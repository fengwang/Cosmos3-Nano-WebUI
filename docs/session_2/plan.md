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
mkdir -p "$SCRATCH/fp8-fix" && cd "$SCRATCH"
export GIT_LFS_SKIP_SMUDGE=1
git clone https://huggingface.co/wfen/Cosmos3-Nano-FP8-Blockwise fp8-fix
cd fp8-fix
git log --oneline -1   # confirm HEAD == 4e181f996abf03f3425298ef692e6e5e56fd46a4
```

**Commit 1 — remove the stale index:**

```bash
git rm model.safetensors.index.json
git commit -m "Remove stale top-level weight index

References 7 non-existent transformer/diffusion_pytorch_model-0000N-of-00007
shards. The real weight is one consolidated transformer/diffusion_pytorch_model.safetensors."
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
for f in config.json checkpoint.json chat_template.json load_quantized.py; do
  head -c 20 "$f"; echo   # must NOT start with "version https://git-lfs"
done
test ! -e model.safetensors.index.json && echo "no stale index: OK"
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
mkdir -p "$SCRATCH/nvfp4-fix" && cd "$SCRATCH"
export GIT_LFS_SKIP_SMUDGE=1
git clone https://huggingface.co/wfen/Cosmos3-Nano-NVFP4-Blockwise nvfp4-fix
cd nvfp4-fix
git log --oneline -1   # confirm HEAD == b5c9332efbaefa72c99890b1b1150da12ca9256c
cat .gitattributes   # re-confirm no blanket *.json/*.py/*.txt/*.jinja line exists
```

**Commit 1:**

```bash
git rm model.safetensors.index.json
git commit -m "Remove stale top-level weight index

References 7 non-existent transformer/model-0000N-of-00007 shards. The real
weight is one consolidated transformer/model.safetensors."
```

**`.gitattributes`:** expected to need **no edit** (already scoped
correctly — confirmed during brainstorming). If the `cat` above shows a
blanket text-extension rule after all, re-derive the removal from NVFP4's
own current content rather than reusing FP8's diff, then proceed as below.

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

Local verification: same shape as Step 2's.

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
rg -n "4e181f99|b5c9332e" .
```

**Check:** the only match is `docs/eval_seed_cases.md`'s own historical
note. Any other match is a hard stop — fix that file and re-run before
proceeding.

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
