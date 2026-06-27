#!/usr/bin/env python3
"""Render the OTA schematic-level SPICE cell from the source spec."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from .spec_io import apply_overrides, load_spec
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import apply_overrides, load_spec


DEVICE_ORDER = ["mn_in", "mp_load", "mn_tail"]


def cell_name(spec: dict[str, Any]) -> str:
    schematic = spec.get("schematic", {})
    if isinstance(schematic, dict) and schematic.get("cell_name"):
        return str(schematic["cell_name"])
    return str(spec.get("design", "ota_5t"))


def device(spec: dict[str, Any], name: str) -> dict[str, Any]:
    devices = spec.get("devices", {})
    if not isinstance(devices, dict) or name not in devices:
        raise ValueError(f"spec is missing devices.{name}")
    values = devices[name]
    if not isinstance(values, dict):
        raise ValueError(f"devices.{name} must be a mapping")
    for key in ["model", "w_um", "l_um", "m"]:
        if key not in values:
            raise ValueError(f"devices.{name} is missing {key}")
    return values


def format_float(value: Any) -> str:
    return f"{float(value):.12g}"


def render_ota_cell(spec: dict[str, Any]) -> str:
    name = cell_name(spec)
    mn_in = device(spec, "mn_in")
    mp_load = device(spec, "mp_load")
    mn_tail = device(spec, "mn_tail")

    return "\n".join(
        [
            f"* SKY130 5T OTA schematic source generated from {spec.get('_meta', {}).get('spec_path', 'spec')}",
            "* Source of truth is the YAML spec; rerun `make netlist-ota` after sizing changes.",
            f".subckt {name} inp inn out vdd vss bias",
            f"+ params: MN_IN_W={format_float(mn_in['w_um'])} MN_IN_L={format_float(mn_in['l_um'])} MN_IN_M={int(mn_in['m'])}",
            f"+ params: MP_LOAD_W={format_float(mp_load['w_um'])} MP_LOAD_L={format_float(mp_load['l_um'])} MP_LOAD_M={int(mp_load['m'])}",
            f"+ params: MN_TAIL_W={format_float(mn_tail['w_um'])} MN_TAIL_L={format_float(mn_tail['l_um'])} MN_TAIL_M={int(mn_tail['m'])}",
            "",
            "* Differential NMOS input pair with single-ended PMOS current-mirror load.",
            f"XMN_INP outn inp tail vss {mn_in['model']} w=MN_IN_W l=MN_IN_L nf=MN_IN_M",
            f"XMN_INN out inn tail vss {mn_in['model']} w=MN_IN_W l=MN_IN_L nf=MN_IN_M",
            f"XMP_DIODE outn outn vdd vdd {mp_load['model']} w=MP_LOAD_W l=MP_LOAD_L nf=MP_LOAD_M",
            f"XMP_MIRROR out outn vdd vdd {mp_load['model']} w=MP_LOAD_W l=MP_LOAD_L nf=MP_LOAD_M",
            f"XMN_TAIL tail bias vss vss {mn_tail['model']} w=MN_TAIL_W l=MN_TAIL_L nf=MN_TAIL_M",
            f".ends {name}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="YAML or JSON OTA spec")
    parser.add_argument("--out", required=True, help="Output SPICE cell path")
    parser.add_argument("--set", action="append", default=[], help="Override, e.g. devices.mn_in.w_um=16")
    args = parser.parse_args()

    spec = apply_overrides(load_spec(args.spec), args.set)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_ota_cell(spec), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
