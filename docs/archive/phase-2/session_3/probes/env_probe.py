"""Action shell: gather hardware/driver facts for the evidence record. Thin subprocess wrapper;
no decision logic lives here — that stays in lib.py's pure checkers.
"""
from __future__ import annotations

import re
import subprocess

# Two observed nvidia-smi header label conventions: the classic "Driver Version: X  CUDA
# Version: Y" and the newer open-kernel-module "KMD Version: X  CUDA UMD Version: Y". Both
# are tried; whichever the installed nvidia-smi actually prints is used.
_DRIVER_PATTERNS = (r"Driver Version:\s*([\d.]+)", r"KMD Version:\s*([\d.]+)")
_CUDA_PATTERNS = (r"CUDA Version:\s*([\d.]+)", r"CUDA UMD Version:\s*([\d.]+)")


def _first_match(patterns: tuple[str, ...], text: str) -> str:
    for pattern in patterns:
        found = re.search(pattern, text)
        if found:
            return found.group(1)
    return "unknown"


def get_hardware_and_driver() -> tuple[str, str]:
    """Return (gpu_name, "driver_version / CUDA cuda_version") via `nvidia-smi`.

    Raises `subprocess.CalledProcessError` if `nvidia-smi` is unavailable or errors — an
    environment failure, not a validation outcome, so it is deliberately left to propagate
    to the caller's single narrow exception boundary rather than masked here.
    """
    name = subprocess.run(
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
        capture_output=True, text=True, check=True, timeout=30,
    ).stdout.strip()
    header = subprocess.run(["nvidia-smi"], capture_output=True, text=True, check=True, timeout=30).stdout
    driver = _first_match(_DRIVER_PATTERNS, header)
    cuda = _first_match(_CUDA_PATTERNS, header)
    return name, f"{driver} / CUDA {cuda}"
