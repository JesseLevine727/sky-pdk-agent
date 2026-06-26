#!/usr/bin/env python3
"""Run and rank a deterministic OTA sizing sweep through run_ngspice.py."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .spec_io import load_spec, target_bounds
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import load_spec, target_bounds


def candidate_overrides(spec_path: str, mode: str) -> list[list[str]]:
    spec = load_spec(spec_path)
    devices = spec["devices"]
    base = {
        "mn_in_w": float(devices["mn_in"]["w_um"]),
        "mn_in_l": float(devices["mn_in"]["l_um"]),
        "mp_load_w": float(devices["mp_load"]["w_um"]),
        "mp_load_l": float(devices["mp_load"]["l_um"]),
        "mn_tail_w": float(devices["mn_tail"]["w_um"]),
        "bias_tail_v": float(spec["bias_tail_v"]),
    }

    if mode == "gain":
        axes = {
            "devices.mn_in.l_um": scale_values(base["mn_in_l"], [1.0, 1.2, 1.4, 1.6, 2.0]),
            "devices.mp_load.l_um": scale_values(base["mp_load_l"], [1.0, 1.2, 1.4, 1.6, 2.0]),
            "devices.mn_in.w_um": scale_values(base["mn_in_w"], [0.9, 1.0, 1.15]),
            "bias_tail_v": clamp_values([base["bias_tail_v"] - 0.04, base["bias_tail_v"], base["bias_tail_v"] + 0.04]),
        }
    elif mode == "broad":
        axes = {
            "devices.mn_in.l_um": scale_values(base["mn_in_l"], [1.0, 1.25, 1.5, 2.0]),
            "devices.mp_load.l_um": scale_values(base["mp_load_l"], [1.0, 1.25, 1.5, 2.0]),
            "devices.mn_in.w_um": scale_values(base["mn_in_w"], [0.8, 1.0, 1.25]),
            "devices.mp_load.w_um": scale_values(base["mp_load_w"], [0.8, 1.0, 1.25]),
            "devices.mn_tail.w_um": scale_values(base["mn_tail_w"], [0.8, 1.0, 1.25]),
            "bias_tail_v": clamp_values([base["bias_tail_v"] - 0.08, base["bias_tail_v"], base["bias_tail_v"] + 0.08]),
        }
    else:
        raise ValueError(f"Unknown sweep mode: {mode}")

    keys = list(axes.keys())
    candidates: list[list[str]] = []
    for values in itertools.product(*(axes[key] for key in keys)):
        candidates.append([f"{key}={value:.6g}" for key, value in zip(keys, values)])
    return candidates


def scale_values(base: float, factors: list[float]) -> list[float]:
    return sorted({round(base * factor, 6) for factor in factors})


def clamp_values(values: list[float], low: float = 0.25, high: float = 1.2) -> list[float]:
    return sorted({round(max(low, min(high, value)), 6) for value in values})


def load_measures(run_dir: Path) -> dict[str, float | None]:
    measures_path = run_dir / "measures.json"
    if not measures_path.exists():
        return {}
    with measures_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def score_candidate(spec: dict[str, Any], measures: dict[str, float | None]) -> dict[str, Any]:
    bounds = target_bounds(spec)
    misses: dict[str, float] = {}
    normalized_margin: dict[str, float] = {}

    for metric, metric_bounds in bounds.items():
        value = measures.get(metric)
        if value is None:
            misses[metric] = math.inf
            normalized_margin[metric] = -math.inf
            continue

        if "min" in metric_bounds:
            target = metric_bounds["min"]
            margin = (float(value) - target) / abs(target)
            normalized_margin[metric] = margin
            if value < target:
                misses[metric] = (target - float(value)) / abs(target)
        if "max" in metric_bounds:
            target = metric_bounds["max"]
            margin = (target - float(value)) / abs(target)
            normalized_margin[metric] = margin
            if value > target:
                misses[metric] = (float(value) - target) / abs(target)

    pass_all = not misses
    total_miss = sum(1e6 if not math.isfinite(value) else value for value in misses.values())
    power = measures.get("power_w")
    gain = measures.get("dc_gain_db")
    ugb = measures.get("unity_gain_hz")
    score = total_miss
    if pass_all:
        score -= 0.01 * float(normalized_margin.get("dc_gain_db", 0.0))
        score -= 0.002 * float(normalized_margin.get("unity_gain_hz", 0.0))
        if power is not None:
            score += float(power) / float(bounds.get("power_w", {}).get("max", 1.0)) * 0.001
    else:
        if gain is not None:
            score -= float(gain) * 1e-5
        if ugb is not None:
            score -= min(float(ugb), 1e8) * 1e-12

    return {
        "pass": pass_all,
        "score": score,
        "misses": misses,
        "normalized_margin": normalized_margin,
    }


def write_markdown_summary(path: Path, ranked: list[dict[str, Any]]) -> None:
    lines = [
        "# OTA Sweep Summary",
        "",
        "| Rank | Pass | Score | Gain dB | UGB Hz | PM deg | Power W | Overrides |",
        "| ---: | :---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for rank, result in enumerate(ranked[:20], start=1):
        measures = result.get("measures", {})
        lines.append(
            "| {rank} | {passed} | {score:.6g} | {gain} | {ugb} | {pm} | {power} | `{overrides}` |".format(
                rank=rank,
                passed="yes" if result["score"]["pass"] else "no",
                score=float(result["score"]["score"]),
                gain=format_metric(measures.get("dc_gain_db")),
                ugb=format_metric(measures.get("unity_gain_hz")),
                pm=format_metric(measures.get("phase_margin_deg")),
                power=format_metric(measures.get("power_w")),
                overrides=", ".join(result.get("overrides", [])),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_metric(value: object) -> str:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return f"{float(value):.6g}"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mode", choices=["gain", "broad"], default="gain")
    parser.add_argument("--max-candidates", type=int, help="Limit candidate count for quick tests")
    args = parser.parse_args()

    spec = load_spec(args.spec)
    script_dir = Path(__file__).resolve().parent
    runner = script_dir / "run_ngspice.py"
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    candidates = candidate_overrides(args.spec, args.mode)
    if args.max_candidates:
        candidates = candidates[: args.max_candidates]

    results: list[dict[str, Any]] = []
    for index, overrides in enumerate(candidates, start=1):
        run_dir = out_root / f"candidate_{index:03d}"
        cmd = [
            sys.executable,
            str(runner),
            "--spec",
            args.spec,
            "--template",
            args.template,
            "--out-dir",
            str(run_dir),
        ]
        for override in overrides:
            cmd.extend(["--set", override])
        if args.dry_run:
            cmd.append("--dry-run")
        completed = subprocess.run(cmd)
        measures = {} if args.dry_run else load_measures(run_dir)
        score = score_candidate(spec, measures) if not args.dry_run else {}
        results.append(
            {
                "candidate": index,
                "overrides": overrides,
                "run_dir": str(run_dir),
                "returncode": completed.returncode,
                "measures": measures,
                "score": score,
            }
        )
        if completed.returncode != 0:
            break

    ranked = sorted(
        results,
        key=lambda item: (
            item["returncode"] != 0,
            not item.get("score", {}).get("pass", False),
            float(item.get("score", {}).get("score", math.inf)),
        ),
    )

    manifest_path = out_root / "sweep_manifest.json"
    ranked_path = out_root / "ranked_results.json"
    summary_path = out_root / "summary.md"
    manifest_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    ranked_path.write_text(json.dumps(ranked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.dry_run:
        write_markdown_summary(summary_path, ranked)

    print(f"Wrote {manifest_path}")
    print(f"Wrote {ranked_path}")
    if not args.dry_run:
        print(f"Wrote {summary_path}")
        best = ranked[0] if ranked else None
        if best:
            print(json.dumps({"best": best}, indent=2, sort_keys=True))
    return 0 if all(item["returncode"] == 0 for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
