"""Spec: trust-boundary — realpath-allowlist containment (INV-8 / EC-S6 / RK-10 / RK-11).

Pure + host-runnable (no GPU): the foundation every later layer depends on. A request-supplied
path must never escape the trusted allowlist (traversal, out-of-mount symlink, or URL scheme).
"""
from __future__ import annotations

import os

import pytest

from preprocessing.paths import UntrustedPathError, resolve_within


def test_traversal_outside_mount_rejected():
    # trust-boundary :: a traversal whose realpath escapes the allowlist is rejected
    with pytest.raises(UntrustedPathError):
        resolve_within("/data/models/../../etc/passwd", ("/data/models",))


def test_path_inside_mount_resolves(tmp_path):
    # trust-boundary :: a path within the allowlisted (resolved) root resolves to its realpath
    root = tmp_path / "models"
    root.mkdir()
    target = root / "Cosmos3-Nano" / "config.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}")
    resolved = resolve_within(str(target), (str(root),))
    assert resolved == os.path.realpath(str(target))


def test_symlink_out_of_mount_rejected(tmp_path):
    # trust-boundary :: a symlink whose realpath leaves the mount is rejected (realpath defeats it)
    root = tmp_path / "models"
    root.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("top secret")
    link = root / "escape.txt"
    os.symlink(str(secret), str(link))
    with pytest.raises(UntrustedPathError):
        resolve_within(str(link), (str(root),))


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data",
        "https://example.com/x.png",
        "file:///etc/passwd",
        "ftp://host/x",
    ],
)
def test_url_scheme_rejected(url):
    # trust-boundary :: URL schemes are rejected outright (no SSRF / no remote load)
    with pytest.raises(UntrustedPathError):
        resolve_within(url, ("/data/models",))


def test_allowlist_prefix_is_not_a_partial_dir_match(tmp_path):
    # trust-boundary :: "/data/models-evil" must not pass an allowlist of "/data/models"
    root = tmp_path / "models"
    root.mkdir()
    sibling = tmp_path / "models-evil"
    sibling.mkdir()
    evil = sibling / "x.txt"
    evil.write_text("x")
    with pytest.raises(UntrustedPathError):
        resolve_within(str(evil), (str(root),))
