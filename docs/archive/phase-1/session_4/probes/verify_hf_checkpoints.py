#!/usr/bin/env python3
"""Torch-free Hugging Face checkpoint verification probe (MIG-S4).

Impure shell (network + filesystem + file write) around a pure core
(parse / derive-precision / cross-check / evaluate-layout / derive-drift / scrub /
build-bundle / render). Reuses ``tools/checkpoint_prep/safetensors_io.py:parse_header``
for header decoding. Imports NEITHER ``torch`` NOR ``diffusers`` (deferred/absent).

Evidence sources:
- HF network (authoritative for what a user downloads): ``git ls-remote`` for the
  revision, ``HfApi.model_info`` for license + card_data, ``list_repo_files`` +
  ``get_paths_info`` for the file manifest with sizes and LFS sha256.
- Local mount (supplemental): safetensors header + config reads, trusted ONLY for a
  file whose local sha256 equals the public LFS sha256 (``local == public``).

Usage:
  python3 docs/session_4/probes/verify_hf_checkpoints.py            # full probe
  python3 docs/session_4/probes/verify_hf_checkpoints.py --check    # pure-core spec assertions
  python3 docs/session_4/probes/verify_hf_checkpoints.py --no-hash  # skip the full-file sha256 gate

The full probe writes ``evidence.json`` + ``summary.md`` into ``--out`` (default: this
probe's own directory). Provenance: every filesystem path is passed through ``scrub``
before it is recorded (R-01).

Cost note: the ``local == public`` gate sha256s only the two probed local files per repo
(the transformer shard + ``quantization_config.json``); with a populated local mount that is
~34 GB / ~80s of reads, and 0 cost when no local mount is present (files absent ->
LOCAL_ABSENT). No large blob is ever downloaded (metadata + partial header reads only).
Transformer-dir discovery here inspects the ``transformer/`` listing; the runtime also tries
``transformer/transformer/`` and the repo root, but neither public repo ships those.
"""
from __future__ import annotations

import argparse
import enum
import hashlib
import json
import os
import pathlib
import struct
import subprocess
import sys

# Reuse the runtime's pure, torch-free safetensors header parser (no new dependency).
# Don't write .pyc into the imported tools/ tree (keep the source tree clean).
sys.dont_write_bytecode = True
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "tools"))
# Resolved at runtime via the sys.path insert above (static analyzers can't follow it).
from checkpoint_prep.safetensors_io import parse_header  # noqa: E402  # pyright: ignore[reportMissingImports]

# --- Public constants -------------------------------------------------------

FP8_REPO = "wfen/Cosmos3-Nano-FP8-Blockwise"
NVFP4_REPO = "wfen/Cosmos3-Nano-NVFP4-Blockwise"
# Declared base_model on the checkpoint cards is nvidia/Cosmos3-Nano; the historical
# local convention dir is wfen/Cosmos3-Nano. Both reachability checks are recorded.
BASE_REPOS = ("nvidia/Cosmos3-Nano", "wfen/Cosmos3-Nano")
DEFAULT_MOUNT_ROOT = "/data/models"  # documented container-mount convention (INV-4)
# Canonical, publishable checkpoint dir names allowed in recorded paths (R-01 allowlist).
ALLOWED_REPO_NAMES = ("Cosmos3-Nano-FP8-Blockwise", "Cosmos3-Nano-NVFP4-Blockwise", "Cosmos3-Nano")
MAX_HEADER_BYTES = 64 * 1024 * 1024  # sanity bound for a safetensors JSON header
HASH_CHUNK = 8 * 1024 * 1024
STUB_CARD_MAX = 512  # a README at or below this many bytes is a stub (frontmatter only), not a usable card
# Public-repo hygiene markers (external artifacts) — existence is recorded, contents never read (R-01).
HYGIENE_MARKERS = ("_s", "load_checkpoint.py", "load_quantized.py", "producer_provenance.json")


# --- Data (enums + records) -------------------------------------------------

class Precision(enum.Enum):
    FP8 = "fp8"
    NVFP4 = "nvfp4"
    UNKNOWN = "unknown"


class Reachability(enum.Enum):
    REACHABLE = "reachable"
    NOT_FOUND = "not_found"
    ERROR = "error"


class CardState(enum.Enum):
    POPULATED = "populated"
    STUB = "stub"
    EMPTY = "empty"
    ABSENT = "absent"


class CrossCheck(enum.Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    LOCAL_ABSENT = "local_absent"
    NO_LFS_SHA = "no_lfs_sha"
    NOT_PROBED = "not_probed"


class SatisfyState(enum.Enum):
    SATISFIED = "satisfied"
    MISSING = "missing"


# --- Pure calculations ------------------------------------------------------

def precision_from_quant_config(cfg: dict) -> tuple[Precision, str]:
    """Pure: map a ``quantization_config.json`` dict to ``(Precision, granularity)``.

    Mirrors ``api/engines/diffusers_oracle/config.py:precision_from_quant_config`` but,
    unlike the runtime, returns ``UNKNOWN`` instead of raising on an unknown/absent
    recipe (the probe records rather than crashes).
    """
    recipe = str(cfg.get("recipe", ""))
    granularity = str(cfg.get("scale_layout", {}).get("granularity", ""))
    if recipe.startswith("nvfp4"):
        return Precision.NVFP4, granularity
    if recipe == "fp8":
        return Precision.FP8, granularity
    return Precision.UNKNOWN, granularity


def precision_from_header_keys(header: dict) -> Precision:
    """Pure: infer precision from safetensors tensor keys.

    Approximates ``diffusers_oracle/loader.py:observe_precision``'s discriminator
    (``_double_scale`` present -> NVFP4). It differs deliberately: ``observe_precision`` is
    binary and defaults to FP8 in the absence of ``_double_scale`` because it runs on a
    *loaded, modelopt-restored* module; this probe reads the *raw header* and so returns
    UNKNOWN when no ``weight_quantizer`` key is present (rather than a spurious FP8).
    """
    keys = [k for k in header if k != "__metadata__"]
    if any(k.endswith("weight_quantizer._double_scale") for k in keys):
        return Precision.NVFP4
    if any(k.endswith("weight_quantizer._scale") for k in keys):
        return Precision.FP8
    return Precision.UNKNOWN


def evaluate_transformer_discovery(files_in_transformer_dir: list[str]) -> tuple[SatisfyState, dict]:
    """Pure: replicate ``discover_transformer_dir``'s requirement over a dir's file list.

    The loader (loader.py:43-47) requires ALL of: at least one ``*.safetensors``,
    ``modelopt_state.pt``, and ``config.json``. Returns (state, per-artifact presence).
    """
    names = {pathlib.PurePosixPath(f).name for f in files_in_transformer_dir}
    have_safetensors = any(n.endswith(".safetensors") for n in names)
    have_modelopt = "modelopt_state.pt" in names
    have_config = "config.json" in names
    presence = {
        "safetensors": have_safetensors,
        "modelopt_state.pt": have_modelopt,
        "config.json": have_config,
    }
    state = SatisfyState.SATISFIED if (have_safetensors and have_modelopt and have_config) else SatisfyState.MISSING
    return state, presence


def crosscheck_sha(local_sha: str | None, public_lfs_sha: str | None) -> CrossCheck:
    """Pure: classify a local-vs-public content comparison for one file."""
    if public_lfs_sha is None:
        return CrossCheck.NO_LFS_SHA
    if local_sha is None:
        return CrossCheck.LOCAL_ABSENT
    return CrossCheck.MATCH if local_sha == public_lfs_sha else CrossCheck.MISMATCH


def card_state_from(readme_size: int | None, stub_max: int = STUB_CARD_MAX) -> CardState:
    """Pure: classify model-card state from the README's byte size (None = file absent).

    A README at or below ``stub_max`` bytes carries at most YAML frontmatter (license,
    base_model) and is a STUB — functionally empty for a public user — distinct from a
    truly-absent file and from a populated card.
    """
    if readme_size is None:
        return CardState.ABSENT
    if readme_size == 0:
        return CardState.EMPTY
    if readme_size <= stub_max:
        return CardState.STUB
    return CardState.POPULATED


def scrub(path: str, mount_root: str = DEFAULT_MOUNT_ROOT, allowed: tuple = ALLOWED_REPO_NAMES) -> str:
    """Pure (R-01): allowlist a filesystem path to the documented mount convention.

    Returns the path unchanged iff it is ``mount_root`` or ``mount_root/<name>[/...]``
    for an allowed public repo name; otherwise ``'<scrubbed>'``. A non-path string
    (no leading ``/``) is returned unchanged (it is metadata such as a repo ID or sha).
    """
    if not path.startswith("/"):
        return path
    if path == mount_root:
        return path
    for name in allowed:
        prefix = f"{mount_root}/{name}"
        if path == prefix or path.startswith(prefix + "/"):
            return path
    return "<scrubbed>"


def hygiene_files(files: list[str]) -> list[str]:
    """Pure (R-01): public-repo files that look like dev-scratch, build-provenance, or
    shipped loader scripts. Their EXISTENCE is recorded for the hygiene drift; their
    CONTENTS are never read (they may carry private build context)."""
    exact = {"load_checkpoint.py", "load_quantized.py", "producer_provenance.json"}
    out = []
    for f in files:
        name = pathlib.PurePosixPath(f).name
        if name.startswith("_") or name in exact:
            out.append(f)
    return sorted(out)


def oracle_loadable(discovery: SatisfyState, quant_cfg_public: bool, precision: Precision) -> bool:
    """Pure: would the imported in-process ``diffusers_oracle`` engine load AND verify this checkpoint?

    Requires ``discover_transformer_dir`` to succeed (``modelopt_state.pt`` + ``*.safetensors`` +
    ``config.json``) AND ``verify_precision`` to resolve a known precision from a present
    ``quantization_config.json`` — the runtime raises on a missing config or on a ``recipe`` that is
    neither exactly ``"fp8"`` nor ``nvfp4*`` (``config.py:precision_from_quant_config``).
    """
    return discovery is SatisfyState.SATISFIED and quant_cfg_public and precision is not Precision.UNKNOWN


def self_containment(files: list[str]) -> dict:
    """Pure: does the manifest ship the diffusers generation-pipeline components?"""
    required_dirs = ("vae", "text_tokenizer", "vision_encoder", "sound_tokenizer", "scheduler")
    required_files = ("model_index.json", "config.json", "generation_config.json")
    dirs_present = {d: any(f.startswith(d + "/") for f in files) for d in required_dirs}
    files_present = {f: (f in files) for f in required_files}
    return {
        "dirs": dirs_present,
        "files": files_present,
        "self_contained": all(dirs_present.values()) and all(files_present.values()),
    }


# --- Pure-core self test (spec-derived assertions) --------------------------

def run_self_check() -> int:
    """Pure spec-derived assertions; no network or filesystem. Returns process code."""
    assert precision_from_header_keys({"blk.weight_quantizer._double_scale": {}}) is Precision.NVFP4
    assert precision_from_header_keys({"blk.weight_quantizer._scale": {}}) is Precision.FP8
    assert precision_from_header_keys({"x.weight": {}, "__metadata__": {}}) is Precision.UNKNOWN

    assert precision_from_quant_config({"recipe": "fp8", "scale_layout": {"granularity": "per-tensor"}}) == (
        Precision.FP8, "per-tensor")
    assert precision_from_quant_config({"recipe": "nvfp4_blockwise_mixed"})[0] is Precision.NVFP4
    assert precision_from_quant_config({})[0] is Precision.UNKNOWN
    # pin the exact-"fp8" semantic the D1/FA-2 finding rests on: the public recipe is
    # 'fp8_blockwise_mixed', which the runtime does NOT accept (a 'startswith' regression must fail).
    assert precision_from_quant_config({"recipe": "fp8_blockwise_mixed"})[0] is Precision.UNKNOWN

    st, pres = evaluate_transformer_discovery(["config.json", "diffusion_pytorch_model.safetensors", "modelopt_state.pt"])
    assert st is SatisfyState.SATISFIED, pres
    st2, pres2 = evaluate_transformer_discovery(["config.json", "model.safetensors", "nvfp4_blockwise_mixed_v1.json", "producer_provenance.json"])
    assert st2 is SatisfyState.MISSING and pres2["modelopt_state.pt"] is False, pres2

    assert crosscheck_sha("aa", "aa") is CrossCheck.MATCH
    assert crosscheck_sha("aa", "bb") is CrossCheck.MISMATCH
    assert crosscheck_sha(None, "bb") is CrossCheck.LOCAL_ABSENT
    assert crosscheck_sha("aa", None) is CrossCheck.NO_LFS_SHA

    assert scrub(f"{DEFAULT_MOUNT_ROOT}/Cosmos3-Nano-FP8-Blockwise") == f"{DEFAULT_MOUNT_ROOT}/Cosmos3-Nano-FP8-Blockwise"
    assert scrub(f"{DEFAULT_MOUNT_ROOT}/Cosmos3-Nano/transformer") == f"{DEFAULT_MOUNT_ROOT}/Cosmos3-Nano/transformer"
    assert scrub("/opt/scratch/unpublished-variant") == "<scrubbed>"
    assert scrub("wfen/Cosmos3-Nano-FP8-Blockwise") == "wfen/Cosmos3-Nano-FP8-Blockwise"

    assert card_state_from(None) is CardState.ABSENT
    assert card_state_from(0) is CardState.EMPTY
    assert card_state_from(62) is CardState.STUB          # NVFP4's 62-byte README is a stub
    assert card_state_from(43813) is CardState.POPULATED  # base repo's real card

    sc = self_containment(["model_index.json", "config.json", "generation_config.json",
                           "vae/x", "text_tokenizer/x", "vision_encoder/x", "sound_tokenizer/x", "scheduler/x"])
    assert sc["self_contained"] is True, sc
    assert self_containment(["config.json"])["self_contained"] is False

    assert hygiene_files(["_s2_postfix.md", "config.json", "load_quantized.py",
                          "transformer/producer_provenance.json"]) == [
        "_s2_postfix.md", "load_quantized.py", "transformer/producer_provenance.json"]
    assert hygiene_files(["config.json", "transformer/model.safetensors"]) == []

    # in-process oracle loadability: FP8's recipe 'fp8_blockwise_mixed' -> UNKNOWN -> not verifiable;
    # NVFP4 fails discovery. Only an exact-'fp8'/'nvfp4*' recipe with full sidecars is loadable.
    assert oracle_loadable(SatisfyState.SATISFIED, True, Precision.FP8) is True
    assert oracle_loadable(SatisfyState.SATISFIED, True, Precision.UNKNOWN) is False
    assert oracle_loadable(SatisfyState.MISSING, False, Precision.UNKNOWN) is False
    # isolate the discovery guard (a regression that dropped it must fail here):
    assert oracle_loadable(SatisfyState.MISSING, True, Precision.FP8) is False

    # torch-free guard
    assert "torch" not in sys.modules and "diffusers" not in sys.modules
    print("self-check: OK (all pure-core spec assertions passed)")
    return 0


# --- Action shell (network + filesystem) ------------------------------------

def ls_remote_head(repo_id: str) -> tuple[Reachability, str | None]:
    """Action: resolve HEAD via ``git ls-remote``. (Reachability, 40-hex sha or None)."""
    url = f"https://huggingface.co/{repo_id}"
    try:
        cp = subprocess.run(["git", "ls-remote", url, "HEAD"], capture_output=True, text=True, timeout=60)
    except (subprocess.TimeoutExpired, OSError):
        return Reachability.ERROR, None
    out = (cp.stdout or "").strip()
    if cp.returncode == 0 and out:
        return Reachability.REACHABLE, out.split()[0]
    if "not found" in (cp.stderr or "").lower() or "repository not found" in (cp.stderr or "").lower():
        return Reachability.NOT_FOUND, None
    return Reachability.ERROR, None


def sha256_file(path: str, do_hash: bool) -> str | None:
    """Action: streaming sha256 of a local file (None if absent or hashing disabled)."""
    if not do_hash or not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(HASH_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def read_local_header(path: str) -> dict | None:
    """Action: partial read of a safetensors file's header (8-byte len + N JSON bytes)."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        prefix = fh.read(8)
        if len(prefix) < 8:
            return None
        n = struct.unpack("<Q", prefix)[0]
        if n <= 0 or n > MAX_HEADER_BYTES:
            return None
        header, _ = parse_header(prefix + fh.read(n))
    return header


def read_local_json(path: str) -> dict | None:
    """Action: read a small local JSON file (None if absent)."""
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return json.load(fh)


def probe_repo(api, repo_id: str, mount_root: str, do_hash: bool) -> dict:
    """Action facade for one checkpoint repo: gather network + local evidence."""
    from huggingface_hub import HfApi  # deferred import (keeps --check dependency-free)
    assert isinstance(api, HfApi)

    reach, ls_sha = ls_remote_head(repo_id)
    info = api.model_info(repo_id)
    card = info.card_data.to_dict() if info.card_data else {}
    files = sorted(api.list_repo_files(repo_id))

    # sizes + LFS sha256 for the whole manifest (one network call)
    paths_info = api.get_paths_info(repo_id, files, expand=True)
    meta: dict[str, dict] = {}
    for o in paths_info:
        lfs = getattr(o, "lfs", None)
        meta[o.path] = {
            "size": getattr(o, "size", None),
            "lfs_sha256": getattr(lfs, "sha256", None) if lfs else None,
        }
    readme_size = meta.get("README.md", {}).get("size")

    local_repo_name = repo_id.split("/")[-1]
    local_root = f"{mount_root}/{local_repo_name}"

    transformer_files = [f for f in files if f.startswith("transformer/")]
    disc_state, disc_presence = evaluate_transformer_discovery(transformer_files)

    # precision from quant config (public presence) + local header (SHA-gated)
    quant_cfg_public = "quantization_config.json" in files
    quant_local_path = f"{local_root}/quantization_config.json"
    quant_cfg_local = read_local_json(quant_local_path) or {}
    prec_from_cfg, granularity = precision_from_quant_config(quant_cfg_local)
    quant_public_sha = meta.get("quantization_config.json", {}).get("lfs_sha256")
    quant_local_sha = sha256_file(quant_local_path, do_hash) if quant_cfg_public else None
    quant_xcheck = crosscheck_sha(quant_local_sha, quant_public_sha) if quant_cfg_public else CrossCheck.NOT_PROBED
    loadable = oracle_loadable(disc_state, quant_cfg_public, prec_from_cfg)

    # locate the transformer safetensors shard(s) and probe the first one's header
    shard_rel = next((f for f in transformer_files if f.endswith(".safetensors")), None)
    header_precision = Precision.UNKNOWN
    header_probe: dict = {"file": shard_rel, "crosscheck": CrossCheck.NOT_PROBED.value}
    if shard_rel is not None:
        local_shard = f"{local_root}/{shard_rel}"
        public_lfs = meta.get(shard_rel, {}).get("lfs_sha256")
        local_sha = sha256_file(local_shard, do_hash)
        xcheck = crosscheck_sha(local_sha, public_lfs)
        header = read_local_header(local_shard)
        if header is not None:
            header_precision = precision_from_header_keys(header)
        header_probe = {
            "file": shard_rel,
            "public_size": meta.get(shard_rel, {}).get("size"),
            "public_lfs_sha256": public_lfs,
            "local_sha256": local_sha,
            "crosscheck": xcheck.value,
            "header_precision": header_precision.value,
            "header_tensor_count": (len([k for k in header if k != "__metadata__"]) if header else None),
            "verified_for_public": xcheck is CrossCheck.MATCH,
        }

    return {
        "repo_id": repo_id,
        "reachability": reach.value,
        "revision_ls_remote": ls_sha,
        "revision_hfapi": info.sha,
        "revision_consistent": (ls_sha == info.sha) if ls_sha else False,
        "license": card.get("license"),
        "base_model": card.get("base_model"),
        "card_state": card_state_from(readme_size).value,
        "readme_size": readme_size,
        "n_files": len(files),
        "top_level": sorted({f.split("/")[0] for f in files}),
        "transformer_files": transformer_files,
        "transformer_discovery": {"state": disc_state.value, "presence": disc_presence},
        "quantization_config_public": quant_cfg_public,
        "quant_recipe": quant_cfg_local.get("recipe"),
        "quant_config_crosscheck": quant_xcheck.value,
        "precision_from_config": prec_from_cfg.value,
        "granularity": granularity,
        "oracle_loadable": loadable,
        "header_probe": header_probe,
        "self_containment": self_containment(files),
        "local_mount": scrub(local_root, mount_root),
        "manifest": {f: meta.get(f, {}) for f in files},
    }


def probe_base_repos(api) -> list[dict]:
    """Action: reachability + (if reachable) license/layout/card of the BF16 base repos.

    The reasoner (``COSMOS3_REASONER_MODEL_DIR``) and the action/forward_dynamics graft
    (``COSMOS3_BASE_ACTION_DIR``) source their BF16 weights from this base, so its public
    availability determines whether those modes are publicly backed.
    """
    rows = []
    for repo in BASE_REPOS:
        reach, sha = ls_remote_head(repo)
        row = {"repo_id": repo, "reachability": reach.value, "revision": sha}
        if reach is Reachability.REACHABLE:
            try:
                info = api.model_info(repo)
                card = info.card_data.to_dict() if info.card_data else {}
                files = sorted(api.list_repo_files(repo))
                readme_size = None
                if "README.md" in files:
                    pi = api.get_paths_info(repo, ["README.md"], expand=True)
                    readme_size = pi[0].size if pi else None
                row.update({
                    "revision_hfapi": info.sha,
                    "gated": bool(getattr(info, "gated", False)),
                    "private": bool(getattr(info, "private", False)),
                    "license": card.get("license"),
                    "n_files": len(files),
                    "has_transformer": any(f.startswith("transformer/") for f in files),
                    "transformer_files": [f for f in files if f.startswith("transformer/")],
                    "has_vision_encoder": any(f.startswith("vision_encoder/") for f in files),
                    "card_state": card_state_from(readme_size).value,
                    "readme_size": readme_size,
                })
            except Exception as exc:  # shell: record as data, never crash the probe
                row["probe_error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    return rows


def derive_drift(repos: list[dict], base_rows: list[dict]) -> list[dict]:
    """Pure: derive the drift set from the gathered per-repo evidence."""
    by_id = {r["repo_id"]: r for r in repos}
    fp8 = by_id.get(FP8_REPO, {})
    nv = by_id.get(NVFP4_REPO, {})
    drifts: list[dict] = []

    # D1: the imported in-process diffusers_oracle engine vs the CURRENT public checkpoints
    not_loadable = [r["repo_id"] for r in (fp8, nv) if r and not r.get("oracle_loadable", True)]
    if not_loadable:
        drifts.append({
            "id": "D1", "severity": "high",
            "summary": ("imported in-process diffusers_oracle engine cannot load+verify the current public "
                        "checkpoints as-is (FP8 recipe is not exact 'fp8'; NVFP4 lacks modelopt_state.pt + "
                        "quantization_config.json). Default generation engine is vllm_omni (separate container "
                        "loader) — verify there in S6/S8."),
            "evidence": {
                "not_loadable_via_oracle": not_loadable,
                "fp8": {"discovery": fp8.get("transformer_discovery", {}).get("state"),
                        "quant_recipe": fp8.get("quant_recipe"),
                        "precision_from_config": fp8.get("precision_from_config"),
                        "quant_config_crosscheck": fp8.get("quant_config_crosscheck")},
                "nvfp4": {"discovery": nv.get("transformer_discovery", {}).get("state"),
                          "presence": nv.get("transformer_discovery", {}).get("presence"),
                          "quant_config_public": nv.get("quantization_config_public"),
                          "header_precision": nv.get("header_probe", {}).get("header_precision")},
            },
        })

    # D2: public availability of the BF16 base (reasoner + action/forward_dynamics)
    reachable_bases = [b["repo_id"] for b in base_rows if b["reachability"] == Reachability.REACHABLE.value]
    notfound_bases = [b["repo_id"] for b in base_rows if b["reachability"] == Reachability.NOT_FOUND.value]
    declared = fp8.get("base_model") or nv.get("base_model")
    if not reachable_bases:
        drifts.append({
            "id": "D2", "severity": "high",
            "summary": "BF16 base model (reasoner + action/forward_dynamics) is not publicly reachable",
            "evidence": {"base_repos": {b["repo_id"]: b["reachability"] for b in base_rows},
                         "declared_base_model": declared},
        })
    elif notfound_bases:
        drifts.append({
            "id": "D2", "severity": "low",
            "summary": ("BF16 base IS public but under a different repo id than the runtime's default "
                        "dir name — document the public base repo id so reasoning/action resolve"),
            "evidence": {"public_base": reachable_bases, "not_found_convention_name": notfound_bases,
                         "declared_base_model": declared},
        })

    # D3: external-repo hygiene — dev-scratch / provenance / loader scripts (existence only)
    hygiene = {r["repo_id"]: hygiene_files(list(r.get("manifest", {}).keys())) for r in repos}
    if any(hygiene.values()):
        drifts.append({
            "id": "D3", "severity": "low",
            "summary": ("public repos ship dev-scratch / build-provenance / loader-script files "
                        "(recommend out-of-band HF-side cleanup; contents not read here)"),
            "evidence": {rid: names for rid, names in hygiene.items() if names},
        })

    # D4: NVFP4 model-card gap (stub/empty/absent) relative to a populated FP8 card (R-04)
    weak = (CardState.STUB.value, CardState.EMPTY.value, CardState.ABSENT.value)
    if nv.get("card_state") in weak:
        drifts.append({
            "id": "D4", "severity": "medium",
            "summary": f"NVFP4 model card is {nv.get('card_state')} ({nv.get('readme_size')} bytes) — R-04",
            "evidence": {"fp8_card": fp8.get("card_state"), "fp8_readme_size": fp8.get("readme_size"),
                         "nvfp4_card": nv.get("card_state"), "nvfp4_readme_size": nv.get("readme_size")},
        })
    return drifts


# --- Bundle + render --------------------------------------------------------

def build_bundle(repos: list[dict], base_rows: list[dict], drifts: list[dict], context: dict) -> dict:
    return {"context": context, "repos": repos, "base_repos": base_rows, "drift": drifts}


def render_summary(bundle: dict) -> str:
    lines = ["# MIG-S4 HF checkpoint verification — probe summary", ""]
    lines.append(f"- generated by: `{bundle['context']['probe']}` (torch-free)")
    lines.append(f"- huggingface_hub: {bundle['context']['hf_hub_version']}")
    lines.append("")
    for r in bundle["repos"]:
        lines.append(f"## {r['repo_id']}")
        lines.append(f"- reachability: {r['reachability']}; revision: {r['revision_hfapi']} "
                     f"(ls-remote consistent: {r['revision_consistent']})")
        lines.append(f"- license: {r['license']}; base_model: {r['base_model']}; card: {r['card_state']}")
        lines.append(f"- files: {r['n_files']}; self-contained (generation): {r['self_containment']['self_contained']}")
        lines.append(f"- transformer discovery (diffusers_oracle): {r['transformer_discovery']['state']} "
                     f"{r['transformer_discovery']['presence']}")
        lines.append(f"- in-process oracle loadable: {r.get('oracle_loadable')} "
                     f"(recipe={r.get('quant_recipe')!r}, precision_from_config={r.get('precision_from_config')})")
        hp = r["header_probe"]
        lines.append(f"- header probe: file={hp.get('file')} precision={hp.get('header_precision')} "
                     f"crosscheck={hp.get('crosscheck')} verified_for_public={hp.get('verified_for_public')}")
        lines.append("")
    lines.append("## base repos (reasoner + action/forward_dynamics source)")
    for b in bundle["base_repos"]:
        if b["reachability"] == "reachable":
            lines.append(f"- {b['repo_id']}: reachable; license={b.get('license')}; "
                         f"gated={b.get('gated')}; transformer={b.get('has_transformer')}; "
                         f"vision_encoder={b.get('has_vision_encoder')}; card={b.get('card_state')}")
        else:
            lines.append(f"- {b['repo_id']}: {b['reachability']}")
    lines.append("")
    lines.append("## drift")
    for d in bundle["drift"]:
        lines.append(f"- {d['id']} ({d['severity']}): {d['summary']}")
    lines.append("")
    return "\n".join(lines)


def run_probe(mount_root: str, out_dir: str, do_hash: bool) -> dict:
    """Action facade: probe both public repos + base reachability, write evidence."""
    from huggingface_hub import HfApi, __version__ as hf_version
    api = HfApi()
    repos = [probe_repo(api, FP8_REPO, mount_root, do_hash),
             probe_repo(api, NVFP4_REPO, mount_root, do_hash)]
    base_rows = probe_base_repos(api)
    drifts = derive_drift(repos, base_rows)
    context = {
        "probe": "docs/session_4/probes/verify_hf_checkpoints.py",
        "hf_hub_version": hf_version,
        "mount_root": scrub(mount_root, mount_root),
        "full_file_hash": do_hash,
    }
    bundle = build_bundle(repos, base_rows, drifts, context)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "evidence.json"), "w") as fh:
        json.dump(bundle, fh, indent=2, sort_keys=True)
    with open(os.path.join(out_dir, "summary.md"), "w") as fh:
        fh.write(render_summary(bundle))
    return bundle


def main() -> int:
    ap = argparse.ArgumentParser(description="MIG-S4 HF checkpoint verification probe")
    ap.add_argument("--check", action="store_true", help="run pure-core spec assertions only")
    ap.add_argument("--mount-root", default=DEFAULT_MOUNT_ROOT, help="local checkpoint mount root")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent), help="output dir")
    ap.add_argument("--no-hash", action="store_true",
                    help="skip the full-file sha256 gate (hashes only the 2 probed local files per repo; "
                         "~34 GB / ~80s when a local mount is present, 0 cost if absent) — cross-check "
                         "downgrades to LOCAL_ABSENT")
    args = ap.parse_args()

    if args.check:
        return run_self_check()

    bundle = run_probe(args.mount_root, args.out, do_hash=not args.no_hash)
    print(render_summary(bundle))
    # Gate: both public repos reachable with consistent revisions + license recorded.
    ok = all(r["reachability"] == Reachability.REACHABLE.value and r["revision_consistent"] and r["license"]
             for r in bundle["repos"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
