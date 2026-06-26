#!/usr/bin/env python3
"""Check local open-source EDA dependencies for this repo."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

try:
    from .tool_env import apply_local_tool_env
except ImportError:  # pragma: no cover - command-line script mode
    from tool_env import apply_local_tool_env


REQUIRED_FOR_SIM = ["ngspice"]
REQUIRED_FOR_SCHEMATIC = ["xschem"]
REQUIRED_FOR_LAYOUT = ["magic", "klayout", "netgen"]


def status_line(name: str) -> tuple[bool, str]:
    path = shutil.which(name)
    if path:
        return True, f"ok      {name}: {path}"
    return False, f"missing {name}"


def check_pdk() -> tuple[bool, list[str]]:
    pdk_root = os.environ.get("PDK_ROOT")
    pdk = os.environ.get("PDK", "sky130A")
    lines: list[str] = []
    if not pdk_root:
        return False, ["missing PDK_ROOT"]
    root = Path(pdk_root)
    model = root / pdk / "libs.tech" / "ngspice" / "sky130.lib.spice"
    magicrc = root / pdk / "libs.tech" / "magic" / f"{pdk}.magicrc"
    netgen_setup = root / pdk / "libs.tech" / "netgen" / f"{pdk}_setup.tcl"
    checks = [("ngspice model", model), ("magic rcfile", magicrc), ("netgen setup", netgen_setup)]
    ok = True
    for label, path in checks:
        exists = path.exists()
        ok = ok and exists
        lines.append(f"{'ok     ' if exists else 'missing'} {label}: {path}")
    return ok, lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soft", action="store_true", help="Always exit 0")
    args = parser.parse_args()

    apply_local_tool_env()

    ok = True
    for tool in REQUIRED_FOR_SIM + REQUIRED_FOR_SCHEMATIC + REQUIRED_FOR_LAYOUT:
        tool_ok, line = status_line(tool)
        ok = ok and tool_ok
        print(line)

    pdk_ok, pdk_lines = check_pdk()
    ok = ok and pdk_ok
    for line in pdk_lines:
        print(line)

    return 0 if ok or args.soft else 1


if __name__ == "__main__":
    raise SystemExit(main())
