#!/usr/bin/env python3
"""Run one analog testbench, score spec targets, and write a durable report."""

from __future__ import annotations

import argparse
import json
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


def run_testbench(spec_path: str, template_path: str, out_dir: Path) -> int:
    runner = Path(__file__).resolve().parent / "run_ngspice.py"
    cmd = [
        sys.executable,
        str(runner),
        "--spec",
        spec_path,
        "--template",
        template_path,
        "--out-dir",
        str(out_dir),
    ]
    return subprocess.run(cmd).returncode


def write_report(path: Path, spec_path: str, template_path: str, out_dir: Path, measures: dict[str, Any], score: dict[str, Any]) -> None:
    lines = [
        "# Single-Testbench Evaluation",
        "",
        f"- Spec: `{spec_path}`",
        f"- Template: `{template_path}`",
        f"- Run dir: `{out_dir}`",
        f"- Overall: {'PASS' if score.get('pass') else 'FAIL'}",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in sorted(measures):
        lines.append(f"| `{key}` | {format_metric(measures.get(key))} |")
    misses = score.get("misses", {})
    if misses:
        lines.extend(["", "## Misses", ""])
        for key, value in sorted(misses.items()):
            lines.append(f"- `{key}` miss `{format_metric(value)}`.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    returncode = run_testbench(args.spec, args.template, out_dir)
    if returncode != 0:
        return returncode
    spec = load_spec(args.spec)
    measures = load_measures(out_dir)
    if "reference_current_a" in spec and "iout_a" in measures and "mirror_error" not in measures:
        reference = float(spec["reference_current_a"])
        measures["mirror_error"] = abs(float(measures["iout_a"]) - reference) / reference
        (out_dir / "measures.json").write_text(json.dumps(measures, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    score = score_candidate(spec, measures)
    evaluation = {"summary": {"pass": score["pass"]}, "measures": measures, "score": score}
    (out_dir / "evaluation.json").write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(Path(args.report), args.spec, args.template, out_dir, measures, score)
    print(f"Wrote {out_dir / 'evaluation.json'}")
    print(f"Wrote {args.report}")
    print(json.dumps(evaluation["summary"], indent=2, sort_keys=True))
    return 2 if args.strict and not score["pass"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
