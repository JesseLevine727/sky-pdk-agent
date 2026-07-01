#!/usr/bin/env python3
"""Render the static CMOS comparator schematic source from a spec."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from .spec_io import load_spec
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import load_spec


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


def number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def render_cell(spec: dict[str, Any]) -> str:
    name = cell_name(spec)
    mn = dev(spec, "mn")
    mp = dev(spec, "mp")
    spec_path = spec.get("_meta", {}).get("spec_path", "spec")
    return "\n".join(
        [
            f"* SKY130 static CMOS comparator schematic source generated from {spec_path}",
            "* Source of truth is the YAML spec; rerun `make netlist-comparator` after sizing changes.",
            f".subckt {name} vin out vdd vss",
            f"+ params: MN_W={number(mn['w_um'])} MN_L={number(mn['l_um'])} MN_M={number(mn.get('m', 1))}",
            f"+ params: MP_W={number(mp['w_um'])} MP_L={number(mp['l_um'])} MP_M={number(mp.get('m', 1))}",
            "",
            "XMN out vin vss vss sky130_fd_pr__nfet_01v8 w=MN_W l=MN_L nf=MN_M",
            "XMP out vin vdd vdd sky130_fd_pr__pfet_01v8 w=MP_W l=MP_L nf=MP_M",
            f".ends {name}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    spec = load_spec(args.spec)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_cell(spec), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
