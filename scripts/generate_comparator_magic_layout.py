#!/usr/bin/env python3
"""Generate a deterministic Magic PCell seed layout for the static comparator."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .generate_ota_magic_layout import (
        _locali_to_m1,
        _m1_h,
        _m1_v,
        _m2_v,
        _point,
        _rect,
        _via1,
        clean_generated_layout,
        mos_call,
    )
    from .spec_io import load_spec
    from .tool_env import apply_local_tool_env
except ImportError:  # pragma: no cover - command-line script mode
    from generate_ota_magic_layout import (
        _locali_to_m1,
        _m1_h,
        _m1_v,
        _m2_v,
        _point,
        _rect,
        _via1,
        clean_generated_layout,
        mos_call,
    )
    from spec_io import load_spec
    from tool_env import apply_local_tool_env


PIN_ORDER = ["vin", "out", "vdd", "vss"]
PIN_ORIGINS = {
    "vin": (-6.0, 6.0),
    "out": (8.0, 6.0),
    "vdd": (8.0, 16.0),
    "vss": (8.0, -4.0),
}
DEVICE_PLACEMENTS = [
    {
        "instance": "XMN",
        "spec_device": "mn",
        "role": "nmos_pull_down",
        "mos_type": "nmos",
        "x_um": 0.0,
        "y_um": 0.0,
    },
    {
        "instance": "XMP",
        "spec_device": "mp",
        "role": "pmos_pull_up",
        "mos_type": "pmos",
        "x_um": 0.0,
        "y_um": 10.0,
    },
]
ROUTE_NETS = ["vin", "out", "vdd", "vss"]
GENERATED_LAYERS = ["locali", "viali", "metal1", "via1", "metal2"]


def cell_name(spec: dict[str, Any]) -> str:
    schematic = spec.get("schematic", {})
    if isinstance(schematic, dict) and schematic.get("cell_name"):
        return str(schematic["cell_name"])
    return str(spec.get("design", "static_comparator"))


def dev(spec: dict[str, Any], name: str) -> dict[str, Any]:
    devices = spec.get("devices", {})
    if not isinstance(devices, dict) or name not in devices:
        raise ValueError(f"spec is missing devices.{name}")
    values = devices[name]
    if not isinstance(values, dict):
        raise ValueError(f"devices.{name} must be a mapping")
    return values


def _pin_point(name: str) -> tuple[float, float]:
    x, y = PIN_ORIGINS[name]
    return (x + 0.5, y + 0.5)


def _nmos_ports(x: float, y: float, values: dict[str, Any]) -> dict[str, tuple[float, float]]:
    w = float(values["w_um"])
    return {
        "B": (x + 0.79, y),
        "D": (x + 0.57, y + w / 2 + 0.785),
        "S": (x + 1.01, y + w / 2 + 0.785),
        "G": (x + 0.79, y + w + 1.06),
    }


def _pmos_ports(x: float, y: float, values: dict[str, Any]) -> dict[str, tuple[float, float]]:
    w = float(values["w_um"])
    return {
        "B": (x + 0.79, y),
        "D": (x + 0.57, y + w / 2 + 0.83),
        "S": (x + 1.01, y + w / 2 + 0.83),
        "G": (x + 0.79, y + w + 1.15),
    }


def _manifest_ports(placement: dict[str, Any], values: dict[str, Any]) -> dict[str, list[float]]:
    x = float(placement["x_um"])
    y = float(placement["y_um"])
    ports = _pmos_ports(x, y, values) if placement["mos_type"] == "pmos" else _nmos_ports(x, y, values)
    return {name: _point(point) for name, point in ports.items()}


def _connect_to_m2(bus_x: float, term: tuple[float, float], route_y: float | None = None) -> list[str]:
    term_x, term_y = term
    y = route_y if route_y is not None else term_y
    lines: list[str] = []
    if abs(y - term_y) > 0.001:
        lines.extend(_m1_v(term_x, term_y, y))
    lines.extend(_m1_h(term_x, bus_x, y))
    lines.extend(_via1(bus_x, y))
    return lines


def route_lines(mn: dict[str, Any], mp: dict[str, Any]) -> list[str]:
    pins = {pin: _pin_point(pin) for pin in PIN_ORDER}
    n = _nmos_ports(0.0, 0.0, mn)
    p = _pmos_ports(0.0, 10.0, mp)
    n_d_route_y = n["D"][1]
    n_s_route_y = n["S"][1]
    p_d_route_y = p["D"][1]
    p_s_route_y = p["S"][1]

    lines = [
        "",
        "# Comparator route seed: metal1 device stubs, metal2 vertical buses.",
    ]
    for body in [n["B"], p["B"]]:
        lines.extend(_locali_to_m1(*body))

    lines.append("# net vin")
    lines.extend(_m2_v(-4.0, n["G"][1] - 0.6, p["G"][1] + 0.6))
    lines.extend(_connect_to_m2(-4.0, pins["vin"]))
    lines.extend(_connect_to_m2(-4.0, n["G"]))
    lines.extend(_connect_to_m2(-4.0, p["G"]))

    out_bus_x = -1.0
    lines.append("# net out")
    lines.extend(_m2_v(out_bus_x, n_d_route_y - 0.6, p_d_route_y + 0.6))
    lines.extend(_connect_to_m2(out_bus_x, pins["out"]))
    lines.extend(_connect_to_m2(out_bus_x, n["D"], n_d_route_y))
    lines.extend(_connect_to_m2(out_bus_x, p["D"], p_d_route_y))

    lines.append("# net vdd")
    lines.extend(_m2_v(9.0, p["B"][1] - 0.6, pins["vdd"][1] + 0.6))
    lines.extend(_connect_to_m2(9.0, pins["vdd"]))
    lines.extend(_connect_to_m2(9.0, p["B"]))
    lines.extend(_connect_to_m2(9.0, p["S"], p_s_route_y))

    lines.append("# net vss")
    lines.extend(_m2_v(10.0, pins["vss"][1] - 0.6, n_s_route_y + 0.6))
    lines.extend(_connect_to_m2(10.0, pins["vss"]))
    lines.extend(_connect_to_m2(10.0, n["B"]))
    lines.extend(_connect_to_m2(10.0, n["S"], n_s_route_y))

    # Give the tiny comparator a stable top-level bounding area for DRC and viewing.
    lines.append("# boundary fill-free marker")
    lines.extend(_rect("metal1", -7.0, -5.0, -6.8, 17.5))
    return lines


def render_tcl(spec: dict[str, Any]) -> str:
    name = cell_name(spec)
    mn = dev(spec, "mn")
    mp = dev(spec, "mp")
    lines = [
        f"# Magic seed layout for {name}; generated from {spec.get('_meta', {}).get('spec_path', 'spec')}.",
        "# This is a deterministic PCell route seed for tool-flow validation.",
        "proc make_pin {name x y num} {",
        "    units microns",
        "    box position $x $y",
        "    box size 1 1",
        "    paint metal1",
        "    label $name FreeSans 1 0 0 0 c metal1",
        "    port make $num",
        "}",
        "",
        f"load {name} -force",
        "units microns",
    ]
    for placement in DEVICE_PLACEMENTS:
        values = dev(spec, str(placement["spec_device"]))
        lines.extend(
            mos_call(
                str(values["model"]),
                str(placement["instance"]),
                values,
                float(placement["x_um"]),
                float(placement["y_um"]),
            )
        )
    for index, pin in enumerate(PIN_ORDER):
        pin_x, pin_y = PIN_ORIGINS[pin]
        lines.append(f"make_pin {pin} {pin_x:.3f} {pin_y:.3f} {index}")
    lines.append("proc draw_routes {} {")
    for line in route_lines(mn, mp):
        lines.append(f"    {line}" if line else "")
    lines.append("}")
    lines.append("draw_routes")
    lines.extend([f"save {name}", "writeall force", "quit -noprompt", ""])
    return "\n".join(lines)


def render_manifest(spec: dict[str, Any], out_dir: Path, tcl_path: Path, mag_path: Path) -> dict[str, Any]:
    name = cell_name(spec)
    return {
        "schema": "sky-pdk-agent.layout_manifest.v1",
        "generator": "scripts/generate_comparator_magic_layout.py",
        "cell": name,
        "design": spec.get("design", name),
        "pdk": spec.get("pdk", "sky130A"),
        "spec": spec.get("_meta", {}).get("spec_path", "spec"),
        "pin_order": PIN_ORDER,
        "pins": [
            {
                "name": pin,
                "port": index,
                "layer": "metal1",
                "origin_um": _point(PIN_ORIGINS[pin]),
                "center_um": _point(_pin_point(pin)),
                "size_um": [1.0, 1.0],
            }
            for index, pin in enumerate(PIN_ORDER)
        ],
        "devices": [
            {
                "instance": placement["instance"],
                "role": placement["role"],
                "spec_device": placement["spec_device"],
                "mos_type": placement["mos_type"],
                "model": dev(spec, str(placement["spec_device"]))["model"],
                "x_um": placement["x_um"],
                "y_um": placement["y_um"],
                "w_um": dev(spec, str(placement["spec_device"]))["w_um"],
                "l_um": dev(spec, str(placement["spec_device"]))["l_um"],
                "source_m": dev(spec, str(placement["spec_device"])).get("m", 1),
                "generated_nf": 1,
                "generated_m": 1,
                "guard_ring": True,
                "ports_um": _manifest_ports(placement, dev(spec, str(placement["spec_device"]))),
            }
            for placement in DEVICE_PLACEMENTS
        ],
        "route_nets": ROUTE_NETS,
        "generated_layers": GENERATED_LAYERS,
        "generated_files": {
            "tcl_seed": str(tcl_path),
            "magic_layout": str(mag_path),
            "magic_log": str(out_dir / f"{name}_layout.log"),
        },
        "notes": [
            "Coordinates are in microns.",
            "This manifest records deterministic generator intent; DRC/LVS/PEX reports remain the signoff gates.",
        ],
    }


def write_manifest(spec: dict[str, Any], out_dir: Path, tcl_path: Path, manifest_path: Path) -> Path:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = render_manifest(spec, out_dir, tcl_path, out_dir / f"{cell_name(spec)}.mag")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--tcl", help="Output Tcl path. Defaults to <out-dir>/static_comparator_seed.tcl")
    parser.add_argument(
        "--manifest",
        help="Output JSON manifest path. Defaults to <out-dir>/<cell>_layout_manifest.json",
    )
    parser.add_argument("--run", action="store_true", help="Run Magic after writing Tcl")
    args = parser.parse_args()
    apply_local_tool_env()

    spec = load_spec(args.spec)
    out_dir = Path(args.out_dir)
    tcl_path = Path(args.tcl) if args.tcl else out_dir / "static_comparator_seed.tcl"
    manifest_path = Path(args.manifest) if args.manifest else out_dir / f"{cell_name(spec)}_layout_manifest.json"
    tcl_path.parent.mkdir(parents=True, exist_ok=True)
    tcl_text = render_tcl(spec)
    tcl_path.write_text(tcl_text, encoding="utf-8")
    print(f"Wrote {tcl_path}")
    manifest_path = write_manifest(spec, out_dir, tcl_path, manifest_path)
    print(f"Wrote {manifest_path}")

    if not args.run:
        return 0
    if not shutil.which("magic"):
        print("missing magic on PATH", file=sys.stderr)
        return 127

    clean_generated_layout(out_dir)
    pdk_root = Path(os.environ.get("PDK_ROOT", str(Path.home() / ".ciel")))
    pdk = os.environ.get("PDK", "sky130A")
    rcfile = pdk_root / pdk / "libs.tech" / "magic" / f"{pdk}.magicrc"
    completed = subprocess.run(
        ["magic", "-dnull", "-noconsole", "-rcfile", str(rcfile)],
        cwd=out_dir,
        input=tcl_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log_path = out_dir / f"{cell_name(spec)}_layout.log"
    log_path.write_text(completed.stdout or "", encoding="utf-8")
    if completed.returncode != 0:
        print(f"Magic layout generation failed. Log: {log_path}", file=sys.stderr)
        tail = "\n".join((completed.stdout or "").splitlines()[-80:])
        if tail:
            print(tail, file=sys.stderr)
        return completed.returncode
    mag_path = out_dir / f"{cell_name(spec)}.mag"
    if not mag_path.exists():
        print(f"Magic did not create {mag_path}", file=sys.stderr)
        print(f"Magic log: {log_path}", file=sys.stderr)
        return 1
    print(f"Magic log: {log_path}")
    print(f"Wrote {mag_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
