"""Trust-boundary path containment (ACD: a pure decision over a realpath; INV-8).

Every request-supplied path is contained to an operator-controlled allowlist BEFORE it is opened
or threaded into any loader. The pickle/`torch.load` checkpoint loaders (``weights_only=False``)
must only ever see env/config dirs — never a request field (RK-10). This guard also rejects URL
schemes outright, so no request can trigger a remote fetch (no SSRF; RK-11).

``os.path.realpath`` is the one Action (it collapses ``..`` and resolves symlinks); the
allowlist-prefix check is a pure Calculation, so containment is host-testable. Raising
``UntrustedPathError`` (vs returning data) is deliberate: a path-escape is a security refusal the
caller maps to 422 and never proceeds past. Refs: session_6/specs/trust-boundary.md; evidence_map H1.
"""
from __future__ import annotations

import os
import re

# A leading URI scheme (http://, https://, file://, ftp://, …). Reject these outright: a trusted
# mount path is always a local filesystem path, never a URL — this is the no-SSRF / no-remote-load gate.
_URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


class UntrustedPathError(Exception):
    """Raised when a request-supplied path escapes the trusted allowlist (→ 422 'untrusted_path').

    Carries the offending input + the allowlist for the error message; never the resolved escape
    target (we do not echo what a traversal pointed at).
    """

    def __init__(self, path: str, allowlist: tuple[str, ...]) -> None:
        self.path = path
        self.allowlist = allowlist
        super().__init__(f"path {path!r} is outside the trusted allowlist {list(allowlist)}")


def is_within(candidate_real: str, root_real: str) -> bool:
    """Pure Calculation: is ``candidate_real`` the root itself or strictly beneath it?

    Compares already-resolved absolute paths with a separator-aware prefix test, so a sibling like
    ``/data/models-evil`` does NOT match the root ``/data/models`` (no partial-component match).
    """
    return candidate_real == root_real or candidate_real.startswith(root_real + os.sep)


def resolve_within(path: str, allowlist: tuple[str, ...]) -> str:
    """Resolve ``path`` and return its realpath iff it lies within an allowlisted root; else raise.

    Steps: reject URL schemes / NUL bytes (no SSRF) → ``realpath`` (Action: collapses ``..``,
    resolves symlinks) → require containment under some allowlisted, *resolved* root (pure). The
    allowlist is operator/config controlled (e.g. the trusted model mount, the artifact volume),
    never request-derived.
    """
    if "\x00" in path or _URL_SCHEME.match(path):
        raise UntrustedPathError(path, allowlist)
    candidate_real = os.path.realpath(path)
    for root in allowlist:
        if is_within(candidate_real, os.path.realpath(root)):
            return candidate_real
    raise UntrustedPathError(path, allowlist)
