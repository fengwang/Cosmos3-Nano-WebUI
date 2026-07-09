# Capability: hf-checkpoint-lfs-layout

Source: `docs/session_2/proposal.md` (New Capabilities)

## ADDED Requirements

### Requirement: No Stale Top-Level Weight Index
Neither `wfen/Cosmos3-Nano-FP8-Blockwise` nor `wfen/Cosmos3-Nano-NVFP4-Blockwise`
MUST ship a top-level `model.safetensors.index.json`. Each repo's `transformer/`
directory MUST be loadable from its single consolidated weight file alone
(`diffusion_pytorch_model.safetensors` for FP8, `model.safetensors` for NVFP4),
with no reference anywhere in the tree to a sharded filename that does not exist.

#### Scenario: Fresh clone has no top-level index file
WHEN a fresh `git clone` of `wfen/Cosmos3-Nano-FP8-Blockwise` (and, separately,
`wfen/Cosmos3-Nano-NVFP4-Blockwise`) is inspected at its new HEAD revision
THEN no `model.safetensors.index.json` exists at the repository root.

#### Scenario: Transformer directory is self-sufficient
WHEN `wfen/Cosmos3-Nano-FP8-Blockwise`'s `transformer/` listing is inspected
THEN it contains exactly one `*.safetensors` weight file, `modelopt_state.pt`,
and `config.json`
AND no filename in the listing matches a `*-0000N-of-00007.safetensors`
sharded-shard pattern.

### Requirement: LFS Tracking By Size And Type
Each repo's `.gitattributes` MUST route a file to Git LFS if and only if the
file is larger than 10 MB or is not plain text (`.safetensors`, `.png`,
`.jpg`/`.jpeg`, `.mp3`, `.mp4`, `.webm`, `.pt`/`.pth`/`.ckpt`, …). A small
plain-text file (`.json`, `.txt`, `.md`, `.jinja`, tokenizer files) MUST be
tracked as a regular Git blob so it resolves on a plain `git clone`, with no
blanket extension-based LFS rule overriding this for a file under the size
threshold. This rule applies repository-wide, including files under
dev-scratch paths (`assets/FP8-Examples/**`, `_s2_*.md`,
`producer_provenance.json`, `load_quantized.py`, etc.) — their storage
mechanism is corrected like any other file; their content, name, and location
are unaffected.

#### Scenario: Small plain-text file is not LFS
WHEN `git lfs ls-files` is run against the new HEAD of
`wfen/Cosmos3-Nano-FP8-Blockwise`
THEN `config.json`, `checkpoint.json`, `chat_template.json`,
`generation_config.json`, `load_checkpoint.py`, `load_quantized.py`,
`text_tokenizer/chat_template.jinja`, `tokenizer_config.json`, and every
`assets/*.json` fixture do NOT appear in its output.

#### Scenario: Oversized tokenizer file remains LFS
WHEN `git lfs ls-files` is run against the new HEAD of either repo
THEN `text_tokenizer/tokenizer.json` (11.4 MB, over the 10 MB threshold)
DOES appear in its output, unchanged from before the fix.

#### Scenario: Dev-scratch file storage mechanism is corrected, content untouched
WHEN `wfen/Cosmos3-Nano-NVFP4-Blockwise`'s `transformer/producer_provenance.json`
is inspected at the new HEAD
THEN it is a regular Git blob, not an LFS pointer
AND its file content and path are byte-identical to the pre-fix revision.

### Requirement: No Large Weight File Is De-LFS'd By The Fix
The set of LFS-tracked large weight files (`transformer/*.safetensors` or
`transformer/model.safetensors`, `vae/diffusion_pytorch_model.safetensors`,
`vision_encoder/model.safetensors`, `sound_tokenizer/diffusion_pytorch_model.safetensors`,
`transformer/modelopt_state.pt`) MUST have identical LFS object OIDs before
and after the `.gitattributes` fix and renormalize commit.

#### Scenario: Large-file OIDs are unchanged across the renormalize commit
WHEN `git lfs ls-files` output for the large weight files is diffed between
the commit immediately before and immediately after the `.gitattributes`
renormalize commit, for either repo
THEN every large weight file's OID (first column) is identical in both
listings.

### Requirement: Orphaned LFS-Pointer Content Is Restored For Compliance Docs
`BIAS.md`, `EXPLAINABILITY.md`, `PRIVACY.md`, and `SAFETY.md` in both repos
MUST contain their real content, not LFS-pointer-spec text, after this
session. Neither the `.gitattributes` fix nor `git add --renormalize .`
resolves this on its own, since no attribute rule has ever matched `.md`;
restoring these four requires a direct LFS object fetch and manual smudge.
FP8's `_s2_postfix.md`, `_s2_rerun.md`, and `_s2_verify.md` have the
identical corruption and are explicitly exempted (dev-scratch, Owner
Decision 3) — this requirement does not apply to them.

#### Scenario: Compliance docs contain real content after the fix
WHEN `BIAS.md`, `EXPLAINABILITY.md`, `PRIVACY.md`, and `SAFETY.md` are read
from a fresh clone of either repo at the new HEAD
THEN none of their first lines is `version https://git-lfs.github.com/spec/v1`
AND each file's byte size matches its known real size (4720, 3189, 1215,
and 3677 bytes respectively).

#### Scenario: Dev-scratch orphans are explicitly left corrupted
WHEN `_s2_postfix.md`, `_s2_rerun.md`, and `_s2_verify.md` are read from a
fresh clone of `wfen/Cosmos3-Nano-FP8-Blockwise` at the new HEAD
THEN they remain LFS-pointer-shaped text, byte-identical to the pre-fix
revision — unchanged, not newly broken and not newly fixed.

#### Scenario: No other orphan survives unnoticed
WHEN every file that is not one of the known large/binary patterns is
inspected in the working clone immediately before the renormalize commit
THEN none of their contents begins with `version https://git-lfs.github.com/spec/v1`
AND any file that does is treated as a newly-discovered orphan requiring
the same fetch-and-smudge treatment, not a silently-accepted gap.

### Requirement: Push Requires A Recorded Owner Go-Ahead
Neither repo MUST be pushed to without an explicit, separately recorded owner
go-ahead immediately preceding that specific push (`project_contract.md`
INV-7).

#### Scenario: FP8 go-ahead precedes the FP8 push
WHEN the commits fixing `wfen/Cosmos3-Nano-FP8-Blockwise` are pushed
THEN a recorded owner go-ahead for that push exists in the session transcript
immediately before the `git push` command runs.

#### Scenario: NVFP4 go-ahead precedes the NVFP4 push, independently
WHEN the commits fixing `wfen/Cosmos3-Nano-NVFP4-Blockwise` are pushed
THEN a recorded owner go-ahead for that push exists, separate from the FP8
go-ahead, immediately before that `git push` command runs.
