#!/usr/bin/env python3
"""Evaluate an OTA spec across named simulation cases."""

from __future__ import annotations

import argparse
import html
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .spec_io import load_spec
    from .sweep_ota import format_metric, load_measures, score_candidate
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import load_spec
    from sweep_ota import format_metric, load_measures, score_candidate


MetricValue = float | int | str | bool | None


METRIC_ORDER = ["dc_gain_db", "unity_gain_hz", "phase_margin_deg", "power_w"]
METRIC_LABELS = {
    "dc_gain_db": "Gain dB",
    "unity_gain_hz": "UGB Hz",
    "phase_margin_deg": "PM deg",
    "power_w": "Power W",
}


def evaluation_cases(spec: dict[str, Any]) -> list[dict[str, Any]]:
    evaluation = spec.get("evaluation", {})
    raw_cases = evaluation.get("cases", {}) if isinstance(evaluation, dict) else {}
    if not raw_cases:
        return [
            {
                "name": "nominal",
                "description": "Nominal operating case from the source spec.",
                "overrides": {},
            }
        ]

    cases: list[dict[str, Any]] = []
    if isinstance(raw_cases, dict):
        iterable = raw_cases.items()
    elif isinstance(raw_cases, list):
        iterable = ((str(item.get("name", f"case_{index:03d}")), item) for index, item in enumerate(raw_cases, start=1))
    else:
        raise ValueError("evaluation.cases must be a mapping or list")

    for name, case in iterable:
        if not isinstance(case, dict):
            raise ValueError(f"evaluation case {name!r} must be a mapping")
        overrides = case.get("overrides", {})
        if overrides is None:
            overrides = {}
        if not isinstance(overrides, dict):
            raise ValueError(f"evaluation case {name!r} overrides must be a mapping")
        cases.append(
            {
                "name": sanitize_case_name(str(name)),
                "description": str(case.get("description", "")),
                "overrides": overrides,
            }
        )
    return cases


def sanitize_case_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in name.strip())
    return cleaned or "case"


def override_args(overrides: dict[str, MetricValue]) -> list[str]:
    args: list[str] = []
    for key in sorted(overrides):
        args.extend(["--set", f"{key}={override_value(overrides[key])}"])
    return args


def override_value(value: MetricValue) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.12g}"
    if value is None:
        return "null"
    return str(value)


def run_case(
    runner: Path,
    spec_path: str,
    template_path: str,
    out_root: Path,
    case: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    run_dir = out_root / str(case["name"])
    cmd = [
        sys.executable,
        str(runner),
        "--spec",
        spec_path,
        "--template",
        template_path,
        "--out-dir",
        str(run_dir),
    ]
    cmd.extend(override_args(case["overrides"]))
    if dry_run:
        cmd.append("--dry-run")

    completed = subprocess.run(cmd)
    measures = {} if dry_run or completed.returncode != 0 else load_measures(run_dir)
    score = {} if dry_run or completed.returncode != 0 else score_candidate(load_spec(spec_path), measures)
    return {
        "case": case["name"],
        "description": case["description"],
        "overrides": case["overrides"],
        "run_dir": str(run_dir),
        "command": cmd,
        "returncode": completed.returncode,
        "measures": measures,
        "score": score,
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    errored = [item for item in results if item["returncode"] != 0]
    failed = [
        item
        for item in results
        if item["returncode"] == 0 and not item.get("score", {}).get("pass", False)
    ]
    passed = [
        item
        for item in results
        if item["returncode"] == 0 and item.get("score", {}).get("pass", False)
    ]
    return {
        "case_count": len(results),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "errored_count": len(errored),
        "pass": not errored and not failed,
    }


def write_markdown_report(path: Path, spec_path: str, template_path: str, out_dir: Path, results: list[dict[str, Any]], plot_path: Path) -> None:
    summary = summarize_results(results)
    lines = [
        "# OTA Evaluation",
        "",
        f"- Spec: `{spec_path}`",
        f"- Template: `{template_path}`",
        f"- Run root: `{out_dir}`",
        f"- Plot: `{plot_path}`",
        f"- Overall: {'PASS' if summary['pass'] else 'FAIL'}",
        "",
        "| Case | Result | Gain dB | UGB Hz | PM deg | Power W | Run Dir |",
        "| --- | :---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in results:
        measures = result.get("measures", {})
        case_pass = result.get("score", {}).get("pass", False)
        if result["returncode"] != 0:
            status = "error"
        else:
            status = "pass" if case_pass else "fail"
        lines.append(
            "| {case} | {status} | {gain} | {ugb} | {pm} | {power} | `{run_dir}` |".format(
                case=result["case"],
                status=status,
                gain=format_metric(measures.get("dc_gain_db")),
                ugb=format_metric(measures.get("unity_gain_hz")),
                pm=format_metric(measures.get("phase_margin_deg")),
                power=format_metric(measures.get("power_w")),
                run_dir=result["run_dir"],
            )
        )

    failures = [result for result in results if result["returncode"] != 0 or not result.get("score", {}).get("pass", False)]
    if failures:
        lines.extend(["", "## Failing Cases", ""])
        for result in failures:
            if result["returncode"] != 0:
                lines.append(f"- `{result['case']}`: simulator returned `{result['returncode']}`.")
                continue
            misses = result.get("score", {}).get("misses", {})
            if misses:
                rendered = ", ".join(f"{key} miss {format_metric(value)}" for key, value in sorted(misses.items()))
                lines.append(f"- `{result['case']}`: {rendered}.")
            else:
                lines.append(f"- `{result['case']}`: no passing score was available.")

    lines.extend(
        [
            "",
            "## Next Agent Moves",
            "",
            "1. Inspect any failing case run directory before changing sizing.",
            "2. Use `make sweep-ota-quick` for a bounded search if failures are coupled.",
            "3. Commit and push after each verified flow improvement or durable design update.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_metric_svg(path: Path, spec: dict[str, Any], results: list[dict[str, Any]]) -> None:
    row_height = 28
    left = 172
    width = 860
    height = 72 + max(1, len(results) * len(METRIC_ORDER)) * row_height
    target_bounds = spec.get("targets", {})
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700">OTA Evaluation Metrics</text>',
        '<line x1="520" y1="50" x2="520" y2="{0}" stroke="#8a8a8a" stroke-dasharray="4 4"/>'.format(height - 18),
        '<text x="524" y="47" font-family="Arial, sans-serif" font-size="11" fill="#555555">target</text>',
    ]
    y = 72
    for result in results:
        measures = result.get("measures", {})
        for metric in METRIC_ORDER:
            label = f"{result['case']} {METRIC_LABELS[metric]}"
            value = measures.get(metric)
            ratio = target_ratio(metric, value, target_bounds)
            bar_width = max(2, min(320, int(320 * ratio / 1.5))) if ratio is not None else 2
            passed = ratio is not None and ratio >= 1.0
            color = "#2f7d32" if passed else "#c62828"
            lines.append(f'<text x="24" y="{y + 17}" font-family="Arial, sans-serif" font-size="12">{html.escape(label)}</text>')
            lines.append(f'<rect x="{left}" y="{y + 5}" width="320" height="14" fill="#eeeeee"/>')
            lines.append(f'<rect x="{left}" y="{y + 5}" width="{bar_width}" height="14" fill="{color}"/>')
            lines.append(
                '<text x="508" y="{y}" font-family="Arial, sans-serif" font-size="12" text-anchor="end">{value}</text>'.format(
                    y=y + 17,
                    value=html.escape(format_metric(value)),
                )
            )
            y += row_height
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def target_ratio(metric: str, value: object, targets: dict[str, Any]) -> float | None:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return None
    config = targets.get(metric, {})
    if not isinstance(config, dict):
        return None
    if "min" in config:
        minimum = float(config["min"])
        return float(value) / minimum if minimum else None
    if "max" in config:
        maximum = float(config["max"])
        return maximum / float(value) if value else None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--report", help="Markdown report path")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when any case misses a target")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    spec = load_spec(args.spec)
    runner = Path(__file__).resolve().parent / "run_ngspice.py"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = [
        run_case(runner, args.spec, args.template, out_dir, case, args.dry_run)
        for case in evaluation_cases(spec)
    ]
    summary = summarize_results(results)

    json_path = out_dir / "evaluation.json"
    plot_path = out_dir / "metrics.svg"
    json_path.write_text(
        json.dumps({"summary": summary, "results": results}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_metric_svg(plot_path, spec, results)
    if args.report:
        write_markdown_report(Path(args.report), args.spec, args.template, out_dir, results, plot_path)

    print(f"Wrote {json_path}")
    print(f"Wrote {plot_path}")
    if args.report:
        print(f"Wrote {args.report}")
    print(json.dumps(summary, indent=2, sort_keys=True))

    if summary["errored_count"]:
        return 1
    if args.strict and not summary["pass"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
