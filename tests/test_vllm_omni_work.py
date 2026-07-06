"""Unit tests for the vllm_omni_work adapter (spec: vllm-omni-generation-adapter).

Injects a fake transport + a tmp artifacts dir — no server, no torch.
"""
from __future__ import annotations

import io
import json
import os

import pytest

from app.schemas import JobStatus
from engines.vllm_omni import work as vw
from engines.vllm_omni.client import (
    FilePart,
    UrllibVideoTransport,
    VideoJobError,
    encode_multipart,
    run_image_job,
)
from jobs.model import JobRecord
from orchestrator.planes import Plane


def _rec(mode="t2v", **params) -> JobRecord:
    params.setdefault("prompt", "a sponge on a plate")
    params.setdefault("width", 640)
    params.setdefault("height", 480)
    params.setdefault("num_frames", 57)
    return JobRecord(id="job-xyz", mode=mode, plane=Plane.GENERATION,
                     status=JobStatus.running, created_at="2026-07-02T00:00:00Z", params=params)


def _fd_rec(**params) -> JobRecord:
    """A forward_dynamics record shaped like the action route's params (no video width/height/num_frames)."""
    params.setdefault("prompt", "Pickup items in the supermarket")
    params.setdefault("domain_name", "agibotworld")
    params.setdefault("chunk_size", 16)
    params.setdefault("raw_action_width", 29)
    params.setdefault("raw_actions", [[0.0] * 29] * 16)
    params.setdefault("resolution_tier", 480)
    return JobRecord(id="job-fd", mode="forward_dynamics", plane=Plane.GENERATION,
                     status=JobStatus.running, created_at="2026-07-02T00:00:00Z", params=params)


class _FakeTransport:
    def __init__(self, *, polls=None, content=b"MP4DATA"):
        self.polls = list(polls or [{"status": "completed", "progress": 100}])
        self.content = content
        self.calls: list[str] = []
        self.last_form: dict | None = None
        self.last_json: dict | None = None
        self.last_path: str | None = None

    def post_form(self, path, form):
        self.calls.append("post")
        self.last_form = form
        self.last_path = path
        return {"id": "vid-1", "status": "queued"}

    def get_json(self, path):
        self.calls.append("get")
        item = self.polls.pop(0)
        return item if isinstance(item, tuple) else (200, item)

    def get_bytes(self, path):
        self.calls.append("content")
        return self.content

    def delete(self, path):
        self.calls.append("delete")

    def post_form_bytes(self, path, form, *, timeout):
        self.calls.append("post_sync")
        self.last_form = form
        self.last_path = path
        return self.content

    def post_json(self, path, obj, *, timeout):
        import base64
        self.calls.append("post_json")
        self.last_json = obj
        self.last_path = path
        return {"data": [{"b64_json": base64.b64encode(self.content).decode()}]}


def test_t2v_routes_to_video_and_writes(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    seen = []
    t = _FakeTransport()
    result = vw.vllm_omni_work(_rec("t2v"), seen.append, transport=t)
    assert "post" in t.calls and "content" in t.calls
    assert result.artifact_path.startswith(str(tmp_path)) and result.artifact_path.endswith(".mp4")
    with open(result.artifact_path, "rb") as fh:
        assert fh.read() == b"MP4DATA"
    assert result.meta["engine"] == "vllm_omni"
    assert seen[-1] == 1.0  # terminal progress emitted by the adapter after write


def test_t2v_audio_sets_sound_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    t = _FakeTransport()
    vw.vllm_omni_work(_rec("t2v_audio", generate_sound=True), lambda _f: None, transport=t)
    assert t.last_form.get("generate_sound") == "true"


def test_meta_carries_param_record(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    t = _FakeTransport()
    result = vw.vllm_omni_work(
        _rec("t2v", seed=123, num_inference_steps=35, guidance_scale=6.0, flow_shift=10.0,
             width=1280, height=720, num_frames=189), lambda _f: None, transport=t)
    m = result.meta
    assert m["seed"] == 123 and m["num_inference_steps"] == 35
    assert m["guidance_scale"] == 6.0 and m["flow_shift"] == 10.0
    assert m["width"] == 1280 and m["height"] == 720 and m["num_frames"] == 189


def test_precision_reflects_the_deployed_checkpoint(tmp_path, monkeypatch):
    # S6: precision is the deployed checkpoint (COSMOS3_CHECKPOINT_LABEL), never a request-supplied value
    # (defends the "WebUI shows NVFP4 but backend served FP8" attribution case).
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", "nvfp4")
    nv = vw.vllm_omni_work(_rec("t2v"), lambda _f: None, transport=_FakeTransport())
    assert nv.meta["precision"] == "nvfp4"
    monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", "fp8")
    # even a (should-never-happen) mismatched param cannot misreport precision
    fp = vw.vllm_omni_work(_rec("t2v", checkpoint="nvfp4"), lambda _f: None, transport=_FakeTransport())
    assert fp.meta["precision"] == "fp8"


def test_adapter_targets_the_single_deployed_endpoint(tmp_path, monkeypatch):
    # With no transport injected, the production transport is built against the single deployed URL.
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("COSMOS3_VLLM_OMNI_URL", "http://vllm-omni:8000")
    captured: dict = {}

    def fake_ctor(base_url):
        captured["base_url"] = base_url
        return _FakeTransport()

    monkeypatch.setattr(vw, "UrllibVideoTransport", fake_ctor)
    vw.vllm_omni_work(_rec("t2v"), lambda _f: None)
    assert captured["base_url"] == "http://vllm-omni:8000"


def test_i2v_submits_input_reference_file_part(tmp_path, monkeypatch):
    # i2v is now wired: the conditioning image rides as an input_reference multipart file part.
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    img = tmp_path / "cond.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    t = _FakeTransport()
    result = vw.vllm_omni_work(_rec("i2v", image_path=str(img)), lambda _f: None, transport=t)
    assert "post" in t.calls and t.last_path == "/v1/videos"
    part = t.last_form.get("input_reference")
    assert isinstance(part, FilePart) and part.data == b"\xff\xd8\xff" and part.content_type == "image/jpeg"
    assert result.artifact_path.endswith(".mp4")


def test_i2v_without_image_fails_typed_no_submit(tmp_path, monkeypatch):
    # No conditioning image → typed error, and NEVER a silent text-only t2v submission.
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    t = _FakeTransport()
    with pytest.raises(VideoJobError) as ei:
        vw.vllm_omni_work(_rec("i2v"), lambda _f: None, transport=t)
    assert ei.value.code == "invalid_input"
    assert "post" not in t.calls


def test_t2i_uses_images_api_and_writes_png(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    t = _FakeTransport(content=b"\x89PNG\r\n\x1a\n")
    result = vw.vllm_omni_work(_rec("t2i", num_frames=1), lambda _f: None, transport=t)
    assert "post_json" in t.calls and "post" not in t.calls
    assert t.last_path == "/v1/images/generations" and t.last_json["response_format"] == "b64_json"
    assert result.artifact_path.endswith(".png")  # image extension, not a video container
    with open(result.artifact_path, "rb") as fh:
        assert fh.read() == b"\x89PNG\r\n\x1a\n"


def test_forward_dynamics_sync_with_action_extra_params(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    frame = tmp_path / "frame.png"
    frame.write_bytes(b"\x89PNG\r\n\x1a\n")
    t = _FakeTransport(content=b"ROLLOUTMP4")
    result = vw.vllm_omni_work(_fd_rec(image_path=str(frame)), lambda _f: None, transport=t)
    assert "post_sync" in t.calls and t.last_path == "/v1/videos/sync"
    ep = json.loads(t.last_form["extra_params"])
    assert ep["action_mode"] == "forward_dynamics" and ep["domain_name"] == "agibotworld"
    assert ep["raw_action_dim"] == 29 and ep["action_chunk_size"] == 16
    assert isinstance(t.last_form["input_reference"], FilePart)
    assert t.last_form["size"] == "640x480" and t.last_form["num_frames"] == "17"  # FD 4:3 tier + chunk+1
    assert result.artifact_path.endswith(".mp4")
    with open(result.artifact_path, "rb") as fh:
        assert fh.read() == b"ROLLOUTMP4"
    # meta must come from the FD source (fd_resolved_params), not the generic video defaults (INV-P5-1):
    m = result.meta
    assert m["precision"] == "fp8" and m["num_frames"] == 17 and m["width"] == 640 and m["height"] == 480
    assert m["num_inference_steps"] == 30 and m["guidance_scale"] == 1.0 and m["flow_shift"] == 5.0


def test_forward_dynamics_without_frame_fails_typed_no_submit(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    t = _FakeTransport()
    with pytest.raises(VideoJobError) as ei:
        vw.vllm_omni_work(_fd_rec(), lambda _f: None, transport=t)  # no image_path
    assert ei.value.code == "invalid_input"
    assert "post_sync" not in t.calls


def test_rejects_escape_conditioning_path_no_submit(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))       # allowlist = artifacts dir
    t = _FakeTransport()
    rec = _rec("i2v", image_path="/etc/passwd")               # outside the allowlist
    with pytest.raises(VideoJobError) as ei:
        vw.vllm_omni_work(rec, lambda _f: None, transport=t)
    assert ei.value.code == "untrusted_path"
    assert "post" not in t.calls                              # rejected before any submit


def test_failure_writes_no_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    t = _FakeTransport(polls=[{"status": "failed", "error": "boom"}])
    with pytest.raises(VideoJobError):
        vw.vllm_omni_work(_rec("t2v"), lambda _f: None, transport=t)
    assert os.listdir(str(tmp_path)) == []                    # no partial artifact


def test_unsupported_mode_raises_no_submit(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    t = _FakeTransport()
    with pytest.raises(VideoJobError) as ei:
        vw.vllm_omni_work(_rec("inverse_dynamics"), lambda _f: None, transport=t)
    assert ei.value.code == "unsupported_mode"
    assert "post" not in t.calls


# --- wire encoding: the real multipart file-part + the production transport methods (review Finding 1) ---


def test_encode_multipart_emits_file_part_and_text_fields():
    form = {"size": "640x480", "input_reference": FilePart("cond.png", "image/png", b"\x89PNG\x00\x01\x02")}
    ctype, body = encode_multipart(form, boundary="B")
    assert ctype == "multipart/form-data; boundary=B"
    assert b'Content-Disposition: form-data; name="size"' in body and b"640x480" in body
    assert b'Content-Disposition: form-data; name="input_reference"; filename="cond.png"' in body
    assert b"Content-Type: image/png" in body
    assert b"\x89PNG\x00\x01\x02" in body  # raw bytes verbatim (not str-coerced)


def _stub_urlopen(monkeypatch, capture: dict, *, body_for):
    class _Resp:
        def __init__(self, data): self._d = data
        def read(self): return self._d
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=None):
        capture["url"] = req.full_url
        capture["method"] = req.get_method()
        capture["headers"] = {k.lower(): v for k, v in req.headers.items()}
        capture["body"] = req.data
        return _Resp(body_for(req.full_url))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)


def test_urllib_transport_post_form_bytes_encodes_multipart(monkeypatch):
    cap: dict = {}
    _stub_urlopen(monkeypatch, cap, body_for=lambda _u: b"ROLLOUT")
    t = UrllibVideoTransport("http://omni:8000")
    out = t.post_form_bytes(
        "/v1/videos/sync", {"size": "640x480", "input_reference": FilePart("f.png", "image/png", b"IMG")}, timeout=30
    )
    assert out == b"ROLLOUT"
    assert cap["url"] == "http://omni:8000/v1/videos/sync" and cap["method"] == "POST"
    assert cap["headers"]["content-type"].startswith("multipart/form-data")
    assert b'filename="f.png"' in cap["body"] and b"IMG" in cap["body"]  # the real wire body carries the image


def test_urllib_transport_post_json_sends_json(monkeypatch):
    cap: dict = {}
    _stub_urlopen(monkeypatch, cap, body_for=lambda _u: json.dumps({"data": [{"b64_json": "AAAA"}]}).encode())
    t = UrllibVideoTransport("http://omni:8000")
    doc = t.post_json("/v1/images/generations", {"prompt": "x", "size": "480x480"}, timeout=30)
    assert doc["data"][0]["b64_json"] == "AAAA"
    assert cap["method"] == "POST" and cap["headers"]["content-type"] == "application/json"
    assert json.loads(cap["body"]) == {"prompt": "x", "size": "480x480"}


def test_post_form_bytes_http_error_is_typed_generation_failed(monkeypatch):
    import urllib.error

    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 500, "err", {}, io.BytesIO(b'{"error":"boom"}'))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    t = UrllibVideoTransport("http://omni:8000")
    with pytest.raises(VideoJobError) as ei:
        t.post_form_bytes("/v1/videos/sync", {"a": "b"}, timeout=5)
    assert ei.value.code == "generation_failed"  # not a bare internal_error


# --- t2i images-response error paths (review Finding 3) ---


class _JsonTransport:
    def __init__(self, doc): self._doc = doc

    def post_json(self, path, obj, *, timeout):
        return self._doc


def test_run_image_job_missing_b64_raises_generation_failed():
    with pytest.raises(VideoJobError) as ei:
        run_image_job(_rec("t2i"), transport=_JsonTransport({"data": []}))
    assert ei.value.code == "generation_failed"


def test_run_image_job_undecodable_b64_raises_generation_failed():
    with pytest.raises(VideoJobError) as ei:
        run_image_job(_rec("t2i"), transport=_JsonTransport({"data": [{"b64_json": "!!!not-base64!!!"}]}))
    assert ei.value.code == "generation_failed"


# --- conditioning image byte cap on the trusted-path branch (review Finding 4; INV-5) ---


def test_i2v_oversized_conditioning_image_rejected_no_submit(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("COSMOS3_MAX_IMAGE_BYTES", "8")  # tiny cap
    img = tmp_path / "big.jpg"
    img.write_bytes(b"\xff\xd8\xff" * 100)  # > 8 bytes
    t = _FakeTransport()
    with pytest.raises(VideoJobError) as ei:
        vw.vllm_omni_work(_rec("i2v", image_path=str(img)), lambda _f: None, transport=t)
    assert ei.value.code == "payload_too_large"
    assert "post" not in t.calls  # rejected before submit
