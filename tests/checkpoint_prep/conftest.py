"""Put the in-repo `tools/` dir on sys.path so `import checkpoint_prep` resolves, and provide shared
synthetic-checkpoint fixtures.

Mirrors how `pyproject.toml [tool.pytest.ini_options] pythonpath = ["api"]` makes `app`/`engines`
importable, but scoped to this test package (the S5 blast radius covers tests/** and tools/**, not
pyproject.toml).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_TOOLS = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

# Config values probed from /data/models/Cosmos3-Nano/transformer/config.json (BF16 source).
CFG = {"action_dim": 64, "hidden_size": 4096, "num_embodiment_domains": 32, "vocab_size": 151936}

ACTION_TENSORS = (
    "action_modality_embed", "action_proj_in.bias.weight", "action_proj_in.fc.weight",
    "action_proj_out.bias.weight", "action_proj_out.fc.weight",
)


def write_safetensors(path: Path, tensors: dict) -> None:
    """tensors: name -> (dtype, shape, payload_bytes). Writes a valid safetensors file (opaque bytes)."""
    from checkpoint_prep.safetensors_io import build_header_bytes

    entries, blob, cursor = {}, bytearray(), 0
    for name, (dtype, shape, payload) in tensors.items():
        entries[name] = {"dtype": dtype, "shape": shape, "data_offsets": [cursor, cursor + len(payload)]}
        blob += payload
        cursor += len(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_header_bytes(entries) + bytes(blob))


def make_fp8_ckpt(root: Path) -> Path:
    """A minimal FP8-dist-like checkpoint dir: transformer/ + config.json + 2 sidecar JSONs."""
    tdir = root / "transformer"
    write_safetensors(tdir / "diffusion_pytorch_model.safetensors", {
        "layers.0.mlp.gate_proj.weight": ("F8_E4M3", [12288, 4096], b"\xab" * 40),
        "layers.0.mlp.gate_proj.weight_quantizer._scale": ("BF16", [96, 32], b"\x11" * 24),
        "self_attn.q_proj.weight": ("BF16", [4096, 4096], b"\x22" * 32),
        "embed_tokens.weight": ("BF16", [151936, 4096], b"\x33" * 48),
        "lm_head.weight": ("F8_E4M3", [151936, 4096], b"\x44" * 40),
        "lm_head.weight_quantizer._amax": ("BF16", [1187, 1, 32, 1], b"\x55" * 16),
        "lm_head.weight_quantizer._scale": ("BF16", [1187, 32], b"\x66" * 16),
    })
    (tdir / "config.json").write_text(json.dumps(
        {**CFG, "action_gen": False, "_class_name": "Cosmos3OmniTransformer"}))
    # Toy is self-consistent: it carries exactly 2 quantized F8 weights (1 mlp + lm_head), so the
    # sidecar counts equal the header's F8-weight count (mirrors real 217 = 216 mlp + 1 lm_head).
    (root / "quantization_config.json").write_text(json.dumps({
        "recipe": "fp8_blockwise_mixed", "quant_lmhead": True,
        "mixed_precision": {"quantized": ["mlp.*", "mlp_moe_gen.*", "lm_head"], "n_quantized": 2},
        "scale_layout": {"n_quantized_weight": 2, "n_scale": 4, "total_scale_elements": 75970,
                         "example_shapes": {"151936x4096": {"module_example": "lm_head"},
                                            "12288x4096": {"module_example": "layers.0.mlp.gate_proj"}}},
    }))
    (root / "quantizer_map_diff.json").write_text(json.dumps({
        "n_weight_quantized": 2, "expected_quantized_count": 2,
        "dropped_action_keys": list(ACTION_TENSORS),
    }))
    return tdir / "diffusion_pytorch_model.safetensors"


def make_bf16_source(root: Path) -> Path:
    """A minimal BF16 source dir carrying the 5 action tensors + BF16 lm_head, distinct byte patterns."""
    h, d, n, v = CFG["hidden_size"], CFG["action_dim"], CFG["num_embodiment_domains"], CFG["vocab_size"]
    shapes = {
        "action_modality_embed": [h], "action_proj_in.bias.weight": [n, h],
        "action_proj_in.fc.weight": [n, d * h], "action_proj_out.bias.weight": [n, d],
        "action_proj_out.fc.weight": [n, d * h], "lm_head.weight": [v, h],
    }
    payloads = {name: bytes([0x70 + i] * 32) for i, name in enumerate(shapes)}
    write_safetensors(root / "transformer" / "diffusion_pytorch_model-00001-of-00002.safetensors",
                      {"action_modality_embed": ("BF16", shapes["action_modality_embed"],
                                                 payloads["action_modality_embed"])})
    write_safetensors(root / "transformer" / "diffusion_pytorch_model-00002-of-00002.safetensors",
                      {k: ("BF16", shapes[k], payloads[k]) for k in shapes if k != "action_modality_embed"})
    return root


@pytest.fixture
def synth(tmp_path):
    """Build a synthetic FP8 checkpoint + BF16 source; return their paths."""
    ck = tmp_path / "fp8"
    st = make_fp8_ckpt(ck)
    src = make_bf16_source(tmp_path / "bf16")
    return SimpleNamespace(ckpt=ck, st=st, source=src, tmp=tmp_path)


# --------------------------------------------------------------------------- S6 self-contained-copy

# The borrowed-file set S6 makes self-contained (S1 inventory §2 + §4, S4 reasoner file set §4).
SC_SHARED_DIRS = ("vae", "text_tokenizer", "vision_encoder", "sound_tokenizer", "scheduler")
SC_ROOT_FILES = ("model_index.json", "config.json", "generation_config.json", "checkpoint.json",
                 "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt",
                 "chat_template.json", "preprocessor_config.json", "video_preprocessor_config.json")
SC_ASSET_FILES = ("example_t2v_prompt.json", "example_t2v_output.mp4", "negative_prompt.json",
                  "example_i2v_prompt.json", "example_i2v_input.jpg", "example_t2vs_prompt.json",
                  "example_action_fd_agibotworld_first_frame.png",
                  "example_action_fd_agibotworld_action_chunks.json",
                  "example_action_fd_agibotworld_4chunk_output.mp4")
SC_REASONER_CONFIGS = ("config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json",
                       "vocab.json", "merges.txt", "chat_template.json", "preprocessor_config.json",
                       "video_preprocessor_config.json")


def make_full_bf16_source(root: Path) -> Path:
    """A complete-enough BF16 source dir: every borrowed file + the reasoner tower, distinct bytes."""
    root.mkdir(parents=True, exist_ok=True)
    # BF16 reasoner/generation tower (copied into <dist>/reasoner/transformer)
    write_safetensors(root / "transformer" / "diffusion_pytorch_model.safetensors", {
        "layers.0.mlp.gate_proj.weight": ("BF16", [8, 4], b"\xa1" * 64),
        "lm_head.weight": ("BF16", [16, 4], b"\xa2" * 128),
    })
    (root / "transformer" / "config.json").write_text(json.dumps({"_class_name": "Cosmos3OmniTransformer"}))
    for d in SC_SHARED_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
        (root / d / "cfg.json").write_text(json.dumps({"component": d, "path_note": "self-contained"}))
        (root / d / "weight.bin").write_bytes(bytes([hash(d) & 0xFF]) * 96)
    for f in SC_ROOT_FILES:
        (root / f).write_text(f"{f}: {{}}\n" if f.endswith((".json", ".txt")) else f)
    (root / "assets").mkdir(parents=True, exist_ok=True)
    for a in SC_ASSET_FILES:
        (root / "assets" / a).write_bytes(f"asset:{a}".encode() + b"\x00" * 8)
    return root


def make_dist_with_symlinks(dist_root: Path, source_root: Path) -> Path:
    """A -dist dir: a REAL (distinct) quantized transformer + every borrowed entry as an absolute
    symlink into the BF16 source (mirrors the real dangling-symlink layout S6 must replace)."""
    dist_root.mkdir(parents=True, exist_ok=True)
    # The quantized generation tower — REAL, byte-distinct from the BF16 source transformer.
    write_safetensors(dist_root / "transformer" / "diffusion_pytorch_model.safetensors", {
        "layers.0.mlp.gate_proj.weight": ("F8_E4M3", [8, 4], b"\xf1" * 32),
        "lm_head.weight": ("BF16", [16, 4], b"\xf2" * 128),
    })
    (dist_root / "transformer" / "config.json").write_text(json.dumps({"action_gen": True}))
    for d in SC_SHARED_DIRS:
        (dist_root / d).symlink_to(source_root / d)
    for f in SC_ROOT_FILES:
        (dist_root / f).symlink_to(source_root / f)
    (dist_root / "assets").symlink_to(source_root / "assets")
    return dist_root


@pytest.fixture
def sc_synth(tmp_path):
    """A -dist-with-symlinks + a full BF16 source, for self-contained-copy tests."""
    src = make_full_bf16_source(tmp_path / "bf16")
    dist = make_dist_with_symlinks(tmp_path / "dist", src)
    return SimpleNamespace(dist=dist, source=src, tmp=tmp_path)
