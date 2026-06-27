#!/usr/bin/env python3
"""Check local open-source EDA dependencies for this repo."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
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


def check_magic_batch() -> tuple[bool, str]:
    if not shutil.which("magic"):
        return False, "missing magic batch probe: magic is not on PATH"
    try:
        completed = subprocess.run(
            ["magic", "-dnull", "-noconsole"],
            input='puts "magic_gencell=[llength [info commands magic::gencell]]"\nexit 0\n',
            text=True,
            capture_output=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return False, "missing magic batch probe: startup timed out"

    output = completed.stdout + completed.stderr
    ok = completed.returncode == 0 and "magic_gencell=1" in output
    if ok:
        return True, "ok      magic batch: magic::gencell available"
    detail = " ".join(output.strip().split())
    return False, f"missing magic batch probe: {detail or f'exit {completed.returncode}'}"


def check_magic_sky130() -> tuple[bool, str]:
    pdk_root = os.environ.get("PDK_ROOT")
    pdk = os.environ.get("PDK", "sky130A")
    if not pdk_root or not shutil.which("magic"):
        return False, "missing magic sky130 probe: PDK_ROOT or magic is missing"
    rcfile = Path(pdk_root) / pdk / "libs.tech" / "magic" / f"{pdk}.magicrc"
    if not rcfile.exists():
        return False, f"missing magic sky130 probe: {rcfile}"
    try:
        completed = subprocess.run(
            ["magic", "-dnull", "-noconsole", "-rcfile", str(rcfile)],
            input='puts "sky130_cmds=[llength [info commands sky130::*]]"\nexit 0\n',
            text=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False, "missing magic sky130 probe: startup timed out"

    output = completed.stdout + completed.stderr
    ok = completed.returncode == 0 and "sky130_cmds=" in output and "sky130_cmds=0" not in output
    if ok:
        version = magic_version()
        return True, f"ok      magic sky130: startup passed{f' ({version})' if version else ''}"
    detail = " ".join(output.strip().split())
    return False, f"missing magic sky130 probe: {detail or f'exit {completed.returncode}'}"


def magic_version() -> str | None:
    try:
        completed = subprocess.run(["magic", "--version"], text=True, capture_output=True, timeout=10)
    except subprocess.TimeoutExpired:
        return None
    version = completed.stdout.strip()
    return version or None


def check_netgen_batch() -> tuple[bool, str]:
    if not shutil.which("netgen"):
        return False, "missing netgen batch probe: netgen is not on PATH"
    try:
        completed = subprocess.run(
            ["netgen", "-batch", "eval", 'puts "netgen_lvs=[llength [info commands lvs]]"'],
            text=True,
            capture_output=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return False, "missing netgen batch probe: startup timed out"

    output = completed.stdout + completed.stderr
    ok = completed.returncode == 0 and "netgen_lvs=1" in output
    if ok:
        return True, "ok      netgen batch: lvs command available"
    detail = " ".join(output.strip().split())
    return False, f"missing netgen batch probe: {detail or f'exit {completed.returncode}'}"


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

    magic_ok, magic_line = check_magic_batch()
    ok = ok and magic_ok
    print(magic_line)

    magic_sky130_ok, magic_sky130_line = check_magic_sky130()
    ok = ok and magic_sky130_ok
    print(magic_sky130_line)

    netgen_ok, netgen_line = check_netgen_batch()
    ok = ok and netgen_ok
    print(netgen_line)

    return 0 if ok or args.soft else 1


if __name__ == "__main__":
    raise SystemExit(main())
