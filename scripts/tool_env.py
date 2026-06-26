#!/usr/bin/env python3
"""Local toolchain environment helpers."""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def prepend_env_path(name: str, entries: list[Path]) -> None:
    existing = os.environ.get(name, "")
    prefix = os.pathsep.join(str(entry) for entry in entries if entry.exists())
    os.environ[name] = prefix + (os.pathsep + existing if existing and prefix else existing)


def apply_local_tool_env() -> None:
    root = repo_root()
    prepend_env_path("PATH", [root / "bin", root / ".tools" / "apt" / "usr" / "bin"])
    prepend_env_path(
        "LD_LIBRARY_PATH",
        [
            root / ".tools" / "apt" / "usr" / "lib" / "klayout",
            root / ".tools" / "apt" / "usr" / "lib" / "x86_64-linux-gnu",
        ],
    )
    os.environ.setdefault("PDK_ROOT", str(Path.home() / ".ciel"))
    os.environ.setdefault("PDK", "sky130A")
    spinit = Path(os.environ["PDK_ROOT"]) / os.environ["PDK"] / "libs.tech" / "ngspice" / "spinit"
    if spinit.exists():
        os.environ.setdefault("SPICEINIT", str(spinit))
