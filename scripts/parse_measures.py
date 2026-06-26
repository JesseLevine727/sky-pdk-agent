#!/usr/bin/env python3
"""Parse ngspice .measure output into JSON."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

MEASURE_RE = re.compile(
    r"^\s*([a-z_][A-Za-z0-9_.$-]*)\s*=\s*"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|nan|inf|-inf)\b"
)
AC_ROW_RE = re.compile(
    r"^\s*\d+\s+"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s+"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s+"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*$"
)
NODE_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_#.$-]*)\s+"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*$"
)


def parse_measure_text(text: str) -> dict[str, float | None]:
    measures: dict[str, float | None] = {}
    for line in text.splitlines():
        match = MEASURE_RE.match(line)
        if not match:
            continue
        name, raw_value = match.groups()
        try:
            value = float(raw_value)
        except ValueError:
            value = None
        if value is not None and not math.isfinite(value):
            value = None
        measures[name] = value
    measures.update(derive_from_printed_tables(text, measures))
    return measures


def derive_from_printed_tables(
    text: str, existing: dict[str, float | None]
) -> dict[str, float]:
    derived: dict[str, float] = {}
    ac_rows = parse_ac_rows(text)
    if ac_rows:
        if existing.get("dc_gain_db") is None:
            derived["dc_gain_db"] = ac_rows[0][1]
        unity = interpolate_unity_gain(ac_rows)
        if unity:
            unity_hz, phase_rad = unity
            derived.setdefault("unity_gain_hz", unity_hz)
            phase_deg = phase_rad * 180.0 / math.pi
            derived.setdefault("phase_at_unity_deg", phase_deg)
            derived.setdefault("phase_margin_deg", 180.0 + phase_deg)

    power = parse_power_from_operating_point(text)
    if power is not None and existing.get("power_w") is None:
        derived["power_w"] = power
    return derived


def parse_ac_rows(text: str) -> list[tuple[float, float, float]]:
    rows: list[tuple[float, float, float]] = []
    in_ac_table = False
    for line in text.splitlines():
        if "frequency" in line and "vdb(out)" in line and "vp(out)" in line:
            in_ac_table = True
            continue
        if not in_ac_table:
            continue
        match = AC_ROW_RE.match(line)
        if match:
            rows.append(tuple(float(value) for value in match.groups()))
    return rows


def interpolate_unity_gain(rows: list[tuple[float, float, float]]) -> tuple[float, float] | None:
    for left, right in zip(rows, rows[1:]):
        f0, gain0, phase0 = left
        f1, gain1, phase1 = right
        if gain0 == 0:
            return f0, phase0
        if gain0 > 0 >= gain1:
            fraction = gain0 / (gain0 - gain1)
            log_f = math.log10(f0) + fraction * (math.log10(f1) - math.log10(f0))
            phase = phase0 + fraction * (phase1 - phase0)
            return 10**log_f, phase
    return None


def parse_power_from_operating_point(text: str) -> float | None:
    vdd_voltage: float | None = None
    vdd_current: float | None = None
    for line in text.splitlines():
        match = NODE_RE.match(line)
        if not match:
            continue
        name, raw_value = match.groups()
        value = float(raw_value)
        if name.lower() == "vdd":
            vdd_voltage = value
        elif name.lower() == "vdd#branch":
            vdd_current = value
    if vdd_voltage is None or vdd_current is None:
        return None
    return abs(vdd_voltage * vdd_current)


def parse_measure_file(path: str | Path) -> dict[str, float | None]:
    return parse_measure_text(Path(path).read_text(encoding="utf-8", errors="replace"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", help="ngspice log or stdout capture")
    parser.add_argument("--out", help="JSON output path")
    args = parser.parse_args()

    measures = parse_measure_file(args.logfile)
    encoded = json.dumps(measures, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
