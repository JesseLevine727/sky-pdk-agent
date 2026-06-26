#!/usr/bin/env python3
"""Propose OTA sizing updates from measured spec misses."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

try:
    from .spec_io import dump_spec, load_spec, target_bounds
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import dump_spec, load_spec, target_bounds


def load_measures(path: str | Path) -> dict[str, float | None]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("measure file must contain a JSON object")
    return data


def scale_device(spec: dict[str, Any], device: str, key: str, factor: float) -> float:
    value = float(spec["devices"][device][key])
    updated = round(value * factor, 6)
    spec["devices"][device][key] = updated
    return updated


def clamp_bias(value: float) -> float:
    return max(0.25, min(1.2, round(value, 6)))


def propose(spec: dict[str, Any], measures: dict[str, float | None]) -> dict[str, Any]:
    proposed_spec = copy.deepcopy(spec)
    proposed_spec.pop("_meta", None)
    bounds = target_bounds(spec)
    overrides: dict[str, float] = {}
    notes: list[str] = []

    gain = measures.get("dc_gain_db")
    gain_min = bounds.get("dc_gain_db", {}).get("min")
    if gain is not None and gain_min is not None and gain < gain_min:
        overrides["devices.mn_in.l_um"] = scale_device(proposed_spec, "mn_in", "l_um", 1.2)
        overrides["devices.mp_load.l_um"] = scale_device(proposed_spec, "mp_load", "l_um", 1.2)
        notes.append("Gain is low; increasing input/load channel length to raise intrinsic gain.")

    ugb = measures.get("unity_gain_hz")
    ugb_min = bounds.get("unity_gain_hz", {}).get("min")
    if ugb is not None and ugb_min is not None and ugb < ugb_min:
        overrides["devices.mn_in.w_um"] = scale_device(proposed_spec, "mn_in", "w_um", 1.25)
        proposed_spec["bias_tail_v"] = clamp_bias(float(proposed_spec["bias_tail_v"]) + 0.05)
        overrides["bias_tail_v"] = proposed_spec["bias_tail_v"]
        notes.append("Unity gain is low; increasing input width and tail bias for more gm.")

    power = measures.get("power_w")
    power_max = bounds.get("power_w", {}).get("max")
    if power is not None and power_max is not None and power > power_max:
        proposed_spec["bias_tail_v"] = clamp_bias(float(proposed_spec["bias_tail_v"]) - 0.05)
        overrides["bias_tail_v"] = proposed_spec["bias_tail_v"]
        overrides["devices.mn_tail.w_um"] = scale_device(proposed_spec, "mn_tail", "w_um", 0.9)
        notes.append("Power is high; reducing tail bias and tail width.")

    pm = measures.get("phase_margin_deg")
    pm_min = bounds.get("phase_margin_deg", {}).get("min")
    if pm is not None and pm_min is not None and pm < pm_min:
        notes.append("Phase margin is low; do not trust a sizing-only fix before inspecting poles and load.")

    if not notes:
        notes.append("No automatic sizing change was triggered by the available measurements.")

    return {
        "overrides": overrides,
        "notes": notes,
        "proposed_spec": proposed_spec,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--measures", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--apply", help="Write proposed spec to this path")
    args = parser.parse_args()

    spec = load_spec(args.spec)
    measures = load_measures(args.measures)
    proposal = propose(spec, measures)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply:
        dump_spec(proposal["proposed_spec"], args.apply)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
