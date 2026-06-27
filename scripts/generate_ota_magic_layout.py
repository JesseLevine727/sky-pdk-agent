#!/usr/bin/env python3
"""Generate a DRC-clean Magic PCell seed layout for the OTA."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .spec_io import load_spec
    from .tool_env import apply_local_tool_env
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import load_spec
    from tool_env import apply_local_tool_env


PIN_ORDER = ["inp", "inn", "out", "vdd", "vss", "bias"]
PIN_ORIGINS = {
    "inp": (-15.0, 24.0),
    "inn": (17.5, 24.0),
    "out": (9.5, 45.0),
    "vdd": (21.5, 45.0),
    "vss": (23.5, -25.0),
    "bias": (-5.0, -25.0),
}


def cell_name(spec: dict[str, Any]) -> str:
    schematic = spec.get("schematic", {})
    if isinstance(schematic, dict) and schematic.get("cell_name"):
        return str(schematic["cell_name"])
    return str(spec.get("design", "ota_5t"))


def dev(spec: dict[str, Any], name: str) -> dict[str, Any]:
    devices = spec.get("devices", {})
    if not isinstance(devices, dict) or name not in devices:
        raise ValueError(f"spec is missing devices.{name}")
    values = devices[name]
    if not isinstance(values, dict):
        raise ValueError(f"devices.{name} must be a mapping")
    return values


def number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def mos_call(model: str, instance: str, values: dict[str, Any], x_um: float, y_um: float) -> list[str]:
    return [
        f"box position {x_um:.3f} {y_um:.3f}",
        (
            f"magic::gencell sky130::{model} {instance} -spice "
            f"w {number(values['w_um'])} l {number(values['l_um'])} "
            "nf 1 m 1 guard 1 doports 1"
        ),
    ]


def _rect(layer: str, x1: float, y1: float, x2: float, y2: float) -> list[str]:
    left, right = sorted((x1, x2))
    bottom, top = sorted((y1, y2))
    return [f"box {left:.3f} {bottom:.3f} {right:.3f} {top:.3f}", f"paint {layer}"]


def _m1_h(x1: float, x2: float, y: float, width: float = 0.2) -> list[str]:
    return _rect("metal1", x1, y - width / 2, x2, y + width / 2)


def _m1_v(x: float, y1: float, y2: float, width: float = 0.2) -> list[str]:
    return _rect("metal1", x - width / 2, y1, x + width / 2, y2)


def _m2_v(x: float, y1: float, y2: float, width: float = 0.5) -> list[str]:
    return _rect("metal2", x - width / 2, y1, x + width / 2, y2)


def _via1(x: float, y: float) -> list[str]:
    lines: list[str] = []
    lines.extend(_rect("metal1", x - 0.35, y - 0.35, x + 0.35, y + 0.35))
    lines.extend(_rect("metal2", x - 0.35, y - 0.35, x + 0.35, y + 0.35))
    lines.extend(_rect("via1", x - 0.17, y - 0.17, x + 0.17, y + 0.17))
    return lines


def _via2(x: float, y: float) -> list[str]:
    lines: list[str] = []
    lines.extend(_rect("metal2", x - 0.35, y - 0.35, x + 0.35, y + 0.35))
    lines.extend(_rect("metal3", x - 0.35, y - 0.35, x + 0.35, y + 0.35))
    lines.extend(_rect("via2", x - 0.18, y - 0.18, x + 0.18, y + 0.18))
    return lines


def _locali_to_m1(x: float, y: float) -> list[str]:
    lines: list[str] = []
    lines.extend(_rect("locali", x - 0.35, y - 0.35, x + 0.35, y + 0.35))
    lines.extend(_rect("metal1", x - 0.35, y - 0.35, x + 0.35, y + 0.35))
    lines.extend(_rect("viali", x - 0.17, y - 0.17, x + 0.17, y + 0.17))
    return lines


def _pin_point(name: str) -> tuple[float, float]:
    x, y = PIN_ORIGINS[name]
    return (x + 0.5, y + 0.5)


def _nmos_ports(x: float, y: float, values: dict[str, Any]) -> dict[str, tuple[float, float]]:
    w = float(values["w_um"])
    l = float(values["l_um"])
    x_mid = x + (1.215 if abs(l - 1.0) < 0.02 else 1.24)
    x_d = x + 0.57
    x_s = x + (1.86 if abs(l - 1.0) < 0.02 else 1.91)
    return {
        "B": (x_mid, y),
        "D": (x_d, y + w / 2 + 0.785),
        "S": (x_s, y + w / 2 + 0.785),
        "G": (x_mid, y + w + 1.06),
    }


def _pmos_ports(x: float, y: float, values: dict[str, Any]) -> dict[str, tuple[float, float]]:
    w = float(values["w_um"])
    return {
        "B": (x + 1.24, y),
        "D": (x + 0.57, y + w / 2 + 0.83),
        "S": (x + 1.91, y + w / 2 + 0.83),
        "G": (x + 1.24, y + w + 1.15),
    }


def _connect(bus_x: float, term: tuple[float, float], route_y: float | None = None) -> list[str]:
    term_x, term_y = term
    y = route_y if route_y is not None else term_y
    lines: list[str] = []
    if abs(y - term_y) > 0.001:
        lines.extend(_m1_v(term_x, term_y, y))
    lines.extend(_m1_h(term_x, bus_x, y))
    lines.extend(_via1(bus_x, y))
    return lines


def _connect_m3_to_m2_bus(bus_x: float, term: tuple[float, float]) -> list[str]:
    term_x, term_y = term
    lines: list[str] = []
    lines.extend(_via1(term_x, term_y))
    lines.extend(_via2(term_x, term_y))
    lines.extend(_rect("metal3", term_x, term_y - 0.25, bus_x, term_y + 0.25))
    lines.extend(_via2(bus_x, term_y))
    return lines


def _route_net(
    name: str,
    bus_x: float,
    connections: list[tuple[tuple[float, float], float | None]],
) -> list[str]:
    del name
    route_points = [route_y if route_y is not None else point[1] for point, route_y in connections]
    y_min = min(route_points) - 0.6
    y_max = max(route_points) + 0.6
    lines = _m2_v(bus_x, y_min, y_max)
    for point, route_y in connections:
        lines.extend(_connect(bus_x, point, route_y))
    return lines


def route_lines(
    mn_in: dict[str, Any],
    mp_load: dict[str, Any],
    mn_tail: dict[str, Any],
) -> list[str]:
    pins = {
        "inp": _pin_point("inp"),
        "inn": _pin_point("inn"),
        "out": _pin_point("out"),
        "vdd": _pin_point("vdd"),
        "vss": _pin_point("vss"),
        "bias": _pin_point("bias"),
    }
    n_inp = _nmos_ports(0.0, 5.0, mn_in)
    n_inn = _nmos_ports(12.0, 5.0, mn_in)
    n_tail = _nmos_ports(6.0, -20.0, mn_tail)
    p_diode = _pmos_ports(0.0, 30.0, mp_load)
    p_mirror = _pmos_ports(12.0, 30.0, mp_load)

    nets = [
        ("inp", -14.0, [(pins["inp"], None), (n_inp["G"], None)]),
        (
            "out",
            10.0,
            [
                (pins["out"], None),
                (n_inn["D"], n_inn["D"][1] - 1.4),
                (p_mirror["D"], p_mirror["D"][1] - 1.4),
            ],
        ),
        (
            "vdd",
            22.0,
            [
                (pins["vdd"], None),
                (p_diode["B"], None),
                (p_mirror["B"], None),
                (p_diode["S"], p_diode["G"][1] + 2.0),
                (p_mirror["S"], p_mirror["G"][1] + 2.0),
            ],
        ),
        (
            "vss",
            24.0,
            [
                (pins["vss"], None),
                (n_inp["B"], None),
                (n_inn["B"], None),
                (n_tail["B"], None),
                (n_tail["S"], n_tail["S"][1] - 1.2),
            ],
        ),
        ("bias", -4.0, [(pins["bias"], None), (n_tail["G"], None)]),
    ]

    lines = [
        "",
        "# Two-layer deterministic route seed: metal1 terminal stubs, metal2 buses.",
        "# Body terminals use local-interconnect-to-metal1 contact stacks.",
    ]
    for body in [p_diode["B"], p_mirror["B"], n_inp["B"], n_inn["B"], n_tail["B"]]:
        lines.extend(_locali_to_m1(*body))
    for name, bus_x, connections in nets:
        lines.append(f"# net {name}")
        lines.extend(_route_net(name, bus_x, connections))

    inn_bus_x = 18.0
    lines.append("# net inn")
    lines.extend(_m2_v(inn_bus_x, n_inn["G"][1] - 0.6, pins["inn"][1] + 0.6))
    lines.extend(_connect(inn_bus_x, pins["inn"]))
    lines.extend(_connect_m3_to_m2_bus(inn_bus_x, n_inn["G"]))

    outn_bus_x = -2.0
    lines.append("# net outn")
    lines.extend(_m2_v(outn_bus_x, n_inp["D"][1] - 0.6, p_mirror["G"][1] + 0.6))
    lines.extend(_connect(outn_bus_x, n_inp["D"]))
    lines.extend(_connect(outn_bus_x, p_diode["D"]))
    lines.extend(_connect_m3_to_m2_bus(outn_bus_x, p_diode["G"]))
    lines.extend(_connect_m3_to_m2_bus(outn_bus_x, p_mirror["G"]))

    tail_left_x = 4.0
    tail_right_x = 20.0
    tail_bridge_y = 0.0
    tail_d_y = n_tail["D"][1] + 1.3
    tail_source_y = n_inp["G"][1] + 2.0
    lines.append("# net tail")
    lines.extend(_m2_v(tail_left_x, tail_d_y - 0.6, tail_bridge_y + 0.6))
    lines.extend(_m2_v(tail_right_x, tail_bridge_y - 0.6, tail_source_y + 0.6))
    lines.extend(_connect(tail_left_x, n_tail["D"], tail_d_y))
    lines.extend(_connect(tail_right_x, n_inp["S"], tail_source_y))
    lines.extend(_connect(tail_right_x, n_inn["S"], tail_source_y))
    lines.extend(_m1_h(tail_left_x, tail_right_x, tail_bridge_y))
    lines.extend(_via1(tail_left_x, tail_bridge_y))
    lines.extend(_via1(tail_right_x, tail_bridge_y))
    return lines


def render_tcl(spec: dict[str, Any]) -> str:
    name = cell_name(spec)
    mn_in = dev(spec, "mn_in")
    mp_load = dev(spec, "mp_load")
    mn_tail = dev(spec, "mn_tail")

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
    lines.extend(mos_call(mp_load["model"], "XMP_DIODE", mp_load, 0.0, 30.0))
    lines.extend(mos_call(mp_load["model"], "XMP_MIRROR", mp_load, 12.0, 30.0))
    lines.extend(mos_call(mn_in["model"], "XMN_INP", mn_in, 0.0, 5.0))
    lines.extend(mos_call(mn_in["model"], "XMN_INN", mn_in, 12.0, 5.0))
    lines.extend(mos_call(mn_tail["model"], "XMN_TAIL", mn_tail, 6.0, -20.0))

    for index, pin in enumerate(PIN_ORDER):
        pin_x, pin_y = PIN_ORIGINS[pin]
        lines.append(f"make_pin {pin} {pin_x:.3f} {pin_y:.3f} {index}")

    lines.append("proc draw_routes {} {")
    for line in route_lines(mn_in, mp_load, mn_tail):
        lines.append(f"    {line}" if line else "")
    lines.append("}")
    lines.append("draw_routes")

    lines.extend(
        [
            f"save {name}",
            "writeall force",
            "quit -noprompt",
            "",
        ]
    )
    return "\n".join(lines)


def clean_generated_layout(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ["*.mag", "*.ext", "*.spice"]:
        for path in out_dir.glob(pattern):
            path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--tcl", help="Output Tcl path. Defaults to <out-dir>/ota_5t_seed.tcl")
    parser.add_argument("--run", action="store_true", help="Run Magic after writing Tcl")
    args = parser.parse_args()
    apply_local_tool_env()

    spec = load_spec(args.spec)
    out_dir = Path(args.out_dir)
    tcl_path = Path(args.tcl) if args.tcl else out_dir / "ota_5t_seed.tcl"
    tcl_path.parent.mkdir(parents=True, exist_ok=True)
    tcl_text = render_tcl(spec)
    tcl_path.write_text(tcl_text, encoding="utf-8")
    print(f"Wrote {tcl_path}")

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
