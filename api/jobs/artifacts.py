"""Local artifact storage (Action shell; E3 + traversal-safe).

Artifacts are written only under `ARTIFACTS_DIR` (the local volume). The filename is derived from a
**sanitized** job id and re-checked with the trust-boundary `resolve_within` (defense-in-depth), so a
crafted id can never traverse out of the directory. S6 produces a deterministic tiny PNG stub (the
real per-mode artifact is S7's engine wiring). Refs: session_6/specs/async-job-model.md.
"""
from __future__ import annotations

import base64
import json
import os
import re

from preprocessing.paths import resolve_within

DEFAULT_ARTIFACTS_DIR = "/srv/artifacts"

# A minimal valid 1x1 PNG — a deterministic, content-type-correct, trivially-retrievable stub (EC-S1).
_STUB_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/Iq6AAAAAElFTkSuQmCC"
)


def artifacts_dir() -> str:
    """Action: the configured artifact volume (defaults to the Compose mount)."""
    return os.environ.get("ARTIFACTS_DIR", DEFAULT_ARTIFACTS_DIR)


def _safe_name(job_id: str) -> str:
    """Pure: reduce a job id to a traversal-proof basename (alnum/_/- only)."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", job_id) or "artifact"


def artifact_path_for(job_id: str, *, directory: str | None = None, ext: str = "png") -> str:
    """Pure-ish: the contained artifact path for a job (sanitized name + realpath-allowlist recheck)."""
    directory = directory or artifacts_dir()
    candidate = os.path.join(directory, f"{_safe_name(job_id)}.{ext}")
    return resolve_within(candidate, (directory,))


def write_stub(job_id: str, *, directory: str | None = None) -> str:
    """Action: write the deterministic stub artifact under the artifact volume; return its path."""
    directory = directory or artifacts_dir()
    os.makedirs(directory, exist_ok=True)
    path = artifact_path_for(job_id, directory=directory)
    with open(path, "wb") as handle:
        handle.write(_STUB_PNG)
    return path


def fetch(job_id: str, *, directory: str | None = None) -> tuple[str, str] | None:
    """Action: ``(path, media_type)`` for a job's artifact, or ``None`` if it does not exist (→ 404)."""
    directory = directory or artifacts_dir()
    path = artifact_path_for(job_id, directory=directory)
    return (path, "image/png") if os.path.exists(path) else None


# --- Real per-mode encoders (S7). Heavy imports (numpy/PIL/imageio) are deferred so this module ---
# --- imports torch-free on the host loop; the encoders run in the worker (the oracle venv/image). ---


def _frames_to_uint8(frames: list) -> list:
    """Deferred-numpy Calculation: HxWx3 float[0,1] (or uint8) frames → a list of uint8 arrays."""
    import numpy as np  # noqa: PLC0415 — deferred; the module stays torch/numpy-free at import

    out = []
    for frame in frames:
        arr = np.asarray(frame)
        if arr.dtype != np.uint8:
            arr = (np.clip(arr, 0.0, 1.0) * 255.0).round().astype(np.uint8)
        out.append(arr)
    return out


def write_image_png(frames: list, job_id: str, *, directory: str | None = None) -> str:
    """Action: write the first frame as a PNG under the artifact volume; return the path (t2i)."""
    from PIL import Image  # noqa: PLC0415 — deferred

    directory = directory or artifacts_dir()
    os.makedirs(directory, exist_ok=True)
    path = artifact_path_for(job_id, directory=directory, ext="png")
    Image.fromarray(_frames_to_uint8(frames[:1])[0]).save(path)
    return path


def write_video_mp4(frames: list, job_id: str, *, fps: int = 24, directory: str | None = None) -> str:
    """Action: write frames as an H.264 MP4 (imageio + the bundled ffmpeg); return the path (t2v/i2v).

    fps default 24 (phase-4 441ad51 cherry-pick, R-06): the model runs at 24 fps; the legacy 16
    mis-encoded duration (E-02/E-03). Used by the dormant diffusers path; the vllm-omni path writes
    server-encoded bytes via ``write_video_bytes`` (no re-encode).
    """
    import imageio.v3 as iio  # noqa: PLC0415 — deferred

    directory = directory or artifacts_dir()
    os.makedirs(directory, exist_ok=True)
    path = artifact_path_for(job_id, directory=directory, ext="mp4")
    iio.imwrite(path, _frames_to_uint8(frames), fps=fps, codec="libx264")
    return path


def write_video_bytes(data: bytes, job_id: str, *, directory: str | None = None) -> str:
    """Action: persist a pre-encoded mp4 (server bytes) verbatim under the artifact volume; return path.

    Byte-passthrough — no re-encode — so the fps and frame count the engine produced are preserved
    exactly (INV-P5-3). The contained path is derived from the sanitized job id and re-checked with
    ``resolve_within`` (INV-8), so a crafted id cannot traverse out of the artifact dir.
    """
    directory = directory or artifacts_dir()
    os.makedirs(directory, exist_ok=True)
    path = artifact_path_for(job_id, directory=directory, ext="mp4")
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def write_latents_npy(latents, job_id: str, *, directory: str | None = None) -> str:
    """Action: persist the pre-VAE M1 latents as ``.npy`` for the endpoint-boundary equivalence test (EC-G1)."""
    import numpy as np  # noqa: PLC0415 — deferred

    directory = directory or artifacts_dir()
    os.makedirs(directory, exist_ok=True)
    path = artifact_path_for(job_id, directory=directory, ext="npy")
    arr = latents.detach().cpu().numpy() if hasattr(latents, "detach") else np.asarray(latents)
    np.save(path, arr)
    return path


def write_trajectory_json(trajectory, job_id: str, *, directory: str | None = None) -> str:
    """Action: write a predicted ``(T, raw_dim)`` trajectory as JSON (stdlib-only); return the path."""
    directory = directory or artifacts_dir()
    os.makedirs(directory, exist_ok=True)
    path = artifact_path_for(job_id, directory=directory, ext="json")
    data = trajectory.tolist() if hasattr(trajectory, "tolist") else list(trajectory)
    with open(path, "w") as handle:
        json.dump(data, handle)
    return path


def _write_wav(path: str, audio, sample_rate: int) -> None:
    """Deferred-numpy Action: write a float audio array as 16-bit PCM WAV (channels inferred)."""
    import wave  # noqa: PLC0415

    import numpy as np  # noqa: PLC0415

    arr = np.asarray(audio, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr[:, None]
    if arr.ndim == 2 and arr.shape[0] < arr.shape[1]:
        arr = arr.T  # coerce [channels, samples] → [samples, channels]
    pcm = (np.clip(arr, -1.0, 1.0) * 32767.0).round().astype("<i2")
    with wave.open(path, "wb") as wav:
        wav.setnchannels(int(arr.shape[1]))
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def _try_mux(video_path: str, wav_path: str) -> str | None:
    """Action: mux the WAV into the MP4 via the bundled ffmpeg; return the canonical path or None on failure."""
    import subprocess  # noqa: PLC0415

    import imageio_ffmpeg  # noqa: PLC0415

    out_path = os.path.splitext(video_path)[0] + ".muxed.mp4"
    try:
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(  # noqa: S603 — fixed absolute ffmpeg exe + a literal arg list (no shell)
            [ffmpeg, "-y", "-i", video_path, "-i", wav_path, "-c:v", "copy", "-c:a", "aac",
             "-shortest", out_path],
            check=True, capture_output=True, timeout=120,
        )
    except Exception:  # noqa: BLE001 — any mux failure degrades to the sidecar WAV (never fail the job)
        return None
    os.replace(out_path, video_path)  # the muxed file takes the canonical .mp4 artifact path
    return video_path


def write_video_with_audio(
    frames: list, audio, job_id: str, *, fps: int = 24, sample_rate: int = 48000,
    directory: str | None = None,
) -> tuple[str, dict]:
    """Action: write an MP4 and mux 48 kHz audio; on failure keep the MP4 + a sidecar WAV (t2v_audio).

    Returns ``(mp4_path, meta)`` with ``meta['audio'] ∈ {'muxed','sidecar','none'}``. Best-effort: the
    audio tensor shape is engine-dependent (EC-G2 confirms it gated-live); a failure never fails the job.
    """
    directory = directory or artifacts_dir()
    video_path = write_video_mp4(frames, job_id, fps=fps, directory=directory)
    if audio is None:
        return video_path, {"audio": "none"}
    wav_path = os.path.splitext(video_path)[0] + ".wav"
    try:
        _write_wav(wav_path, audio, sample_rate)
    except Exception:  # noqa: BLE001 — unknown audio shape: degrade to a silent-but-retrievable MP4
        return video_path, {"audio": "none"}
    muxed = _try_mux(video_path, wav_path)
    if muxed is not None:
        os.remove(wav_path)
        return muxed, {"audio": "muxed"}
    return video_path, {"audio": "sidecar", "audio_path": wav_path}
