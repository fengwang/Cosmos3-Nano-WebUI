"""Generation-plane worker entrypoint — a request-serving worker (Action; deferred heavy import).

S7 turns the S6 idle worker into a **request server**: it loads the action-enabled pipeline ONCE
(`action_gen=True`), wraps the same `pipe` in both a `DiffusersOracleAdapter` (generation — no action
condition) and a `DiffusersActionAdapter` (action), warms it, opens a Unix-domain socket, and **only
then** touches the ready-file (so the orchestrator's READY_FILE probe passes once the socket is
accepting and the model is warm). It then serves one request per connection: dispatch → encode the
artifact → reply. Because inference runs in THIS process group, `os.killpg` eviction stops in-flight
work (INV-4) and the api process never loads a second model.

The pure-ish `dispatch` + the request mappers are host-testable with fake adapters + stubbed encoders;
the real pipeline runs gated-live. Run as ``python -m orchestrator.gen_worker <ready_file>``. The heavy
diffusers imports are deferred into `build_adapters`, so this module imports torch-free. Refs:
session_7/specs/generation-plane-inference-channel.md; design.md D-1/D-2/D-5.
"""
from __future__ import annotations

import contextlib
import os
import socket
import sys

from jobs import artifacts
from jobs.gen_client import DEFAULT_GEN_SOCK, frame, unframe

_GENERATION_MODES = frozenset({"t2i", "t2v", "i2v", "t2v_audio"})


def _to_generation_request(request: dict):
    """Pure mapping: the IPC request → a deterministic ``GenerationRequest`` (engines.base is torch-free)."""
    from engines.base import GenerationRequest, default_dimensions  # noqa: PLC0415 — torch-free, keep local

    params = request.get("params", {})
    p_res = params.get("resolution")
    # Mode-aware default (UX-S2): mirrors the deployed vLLM-Omni path so a COSMOS3_GEN_ENGINE switch
    # never changes the shipped default resolution. Video -> 1280x720, t2i -> 480; explicit values win.
    dw, dh = default_dimensions(request["mode"], int(p_res) if p_res is not None else None)
    return GenerationRequest(
        mode=request["mode"],
        case_id=request.get("job_id", ""),
        prompt=params.get("prompt"),
        negative_prompt=params.get("negative_prompt"),
        image_path=request.get("image_path"),
        generate_sound=bool(params.get("generate_sound")),
        seed=int(params.get("seed", 123)),
        num_frames=int(params.get("num_frames", 1)),
        height=int(params.get("height", dh)),
        width=int(params.get("width", dw)),
        num_inference_steps=int(params.get("num_inference_steps", 8)),
    )


def _to_action_request(request: dict):
    """Pure-ish mapping: the IPC request → an ``ActionRequest`` (numpy deferred; only for FD raw_actions)."""
    from engines.diffusers_action.adapter import ActionRequest  # noqa: PLC0415
    from preprocessing.action_schema import ActionMode  # noqa: PLC0415

    params = request.get("params", {})
    raw = params.get("raw_actions")
    raw_actions = None
    if raw is not None:
        import torch  # noqa: PLC0415 — FD's driving tensor is a torch tensor (the S4 engine contract)

        raw_actions = torch.tensor(raw, dtype=torch.float32)
    return ActionRequest(
        mode=ActionMode(request["mode"]),
        domain_name=str(params.get("domain_name", "")),
        chunk_size=int(params.get("chunk_size", 0)),
        raw_actions=raw_actions,
        image_path=request.get("image_path"),
        video_path=request.get("video_path"),
        resolution_tier=int(params.get("resolution_tier", 480)),
        seed=int(params.get("seed", 123)),
        view_point=str(params.get("view_point", "ego_view")),
        prompt=params.get("prompt"),
        case_id=request.get("job_id", ""),
    )


def _precision_of(info) -> str:
    return info.precision.value if info is not None and info.precision is not None else "unknown"


def _engine_of(info, default: str) -> str:
    return info.engine if info is not None and info.engine else default


def _encode_generation_reply(job_id: str, mode: str, result, *, want_latents: bool) -> dict:
    """Encode a generation result into the per-mode artifact + the reply meta (engine/precision/vram)."""
    meta = {"engine": _engine_of(result.info, "diffusers_oracle"), "precision": _precision_of(result.info),
            "vram_peak_bytes": int(getattr(result, "vram_peak_bytes", 0))}
    if mode == "t2i":
        path = artifacts.write_image_png(result.frames, job_id)
    elif mode == "t2v_audio":
        path, audio_meta = artifacts.write_video_with_audio(result.frames, result.audio, job_id)
        meta.update(audio_meta)
    else:  # t2v, i2v
        path = artifacts.write_video_mp4(result.frames, job_id)
    if want_latents and getattr(result, "latents", None) is not None:
        meta["latents_path"] = artifacts.write_latents_npy(result.latents, job_id)  # EC-G1 boundary check
    return {"ok": True, "artifact_path": path, "meta": meta}


def _encode_action_reply(job_id: str, mode: str, result) -> dict:
    """Encode an action result: ID → trajectory JSON (primary); FD/policy → rollout MP4 + trajectory sidecar."""
    meta = {"engine": _engine_of(result.info, "diffusers_action"), "precision": _precision_of(result.info),
            "vram_peak_bytes": int(getattr(result, "vram_peak_bytes", 0))}
    if mode == "inverse_dynamics":
        return {"ok": True, "artifact_path": artifacts.write_trajectory_json(result.trajectory, job_id), "meta": meta}
    path = artifacts.write_video_mp4(result.frames, job_id)
    if getattr(result, "trajectory", None) is not None:
        meta["trajectory_path"] = artifacts.write_trajectory_json(result.trajectory, job_id)
    return {"ok": True, "artifact_path": path, "meta": meta}


def dispatch(request: dict, gen_adapter, action_adapter, on_progress=None) -> dict:
    """Run one request on the right adapter + encode its artifact → a reply dict (errors-as-data).

    Generation modes use the oracle adapter (no action condition); action modes use the action adapter.
    ``on_progress(step, total)`` is relayed to the oracle adapter for generation requests only.
    Any engine/encode failure becomes a typed ``{ok:false, code:'internal_error'}`` reply (the edge has
    already validated inputs, so a worker-side failure is unexpected → internal).
    """
    job_id, mode = request["job_id"], request["mode"]
    try:
        if request.get("kind") == "action" or mode not in _GENERATION_MODES:
            return _encode_action_reply(job_id, mode, action_adapter.generate_action(_to_action_request(request)))
        result = gen_adapter.generate(_to_generation_request(request), on_progress=on_progress)
        return _encode_generation_reply(job_id, mode, result, want_latents=bool(request.get("want_latents")))
    except Exception as exc:  # noqa: BLE001 — surface as a typed failure reply; the runner fails the job
        return {"ok": False, "code": "internal_error", "message": str(exc)}


def _listen(sock_path: str) -> socket.socket:
    """Action: bind+listen a Unix-domain socket (unlinking any stale path first)."""
    if os.path.exists(sock_path):
        os.unlink(sock_path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(sock_path)
    srv.listen(8)
    return srv


def serve(ready_path: str, gen_adapter, action_adapter, *, sock_path: str | None = None) -> None:
    """Action: listen, signal ready (AFTER listening), then serve one request per connection until killed."""
    srv = _listen(sock_path or os.environ.get("COSMOS3_GEN_SOCK", DEFAULT_GEN_SOCK))
    with open(ready_path, "w") as handle:  # ready ONLY after the socket is accepting (ordering matters)
        handle.write("ready")
    while True:
        conn, _ = srv.accept()
        try:
            def on_progress(step, total, _conn=conn):  # default captures conn at definition, not loop time
                _conn.sendall(frame({"type": "progress", "step": step, "total": total}))

            reply = dispatch(unframe(conn.recv), gen_adapter, action_adapter, on_progress=on_progress)
            conn.sendall(frame({"type": "result", **reply}))
        except Exception as exc:  # noqa: BLE001 — a bad frame/dispatch must not kill the serve loop
            with contextlib.suppress(Exception):
                conn.sendall(frame({"type": "result", "ok": False, "code": "internal_error", "message": str(exc)}))
        finally:
            conn.close()


def build_adapters(cfg):
    """Action (deferred heavy import): one action-enabled pipeline → (oracle-view adapter, action adapter).

    Both adapters wrap the SAME `pipe` (one ~12.8 GiB load): the oracle view runs plain generation (no
    action condition, exact INV-3 reference), the action adapter runs FD/ID/policy. INV-8: the checkpoint
    dir comes only from operator env (`ActionEngineConfig.from_env`), never a request field.

    Pipeline stays GPU-resident (no CPU offload); both adapters use CUDA generator.
    """
    from dataclasses import replace  # noqa: PLC0415

    from engines.diffusers_action.adapter import DiffusersActionAdapter  # noqa: PLC0415
    from engines.diffusers_action.loader import build_action_pipeline, load_action_transformer  # noqa: PLC0415
    from engines.diffusers_oracle.adapter import DiffusersOracleAdapter  # noqa: PLC0415

    transformer, info = load_action_transformer(cfg)
    pipe = build_action_pipeline(cfg, transformer)
    gen_adapter = DiffusersOracleAdapter(pipe, replace(info, engine="diffusers_oracle"), device=cfg.device)
    action_adapter = DiffusersActionAdapter(pipe, info, device=cfg.device)
    return gen_adapter, action_adapter


def main(ready_path: str) -> None:
    """Action: build+warm the action-enabled pipeline (trusted mount), then serve until the group is killed."""
    from engines.diffusers_action.loader import ActionEngineConfig  # noqa: PLC0415

    gen_adapter, action_adapter = build_adapters(ActionEngineConfig.from_env())
    gen_adapter.warm()  # force the model + VAE resident (the real generation-plane footprint)
    serve(ready_path, gen_adapter, action_adapter)


if __name__ == "__main__":
    main(sys.argv[1])
