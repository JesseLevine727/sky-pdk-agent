#!/usr/bin/env python3
"""Run a bounded, file-based analog agent loop for the 5T OTA."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .spec_io import apply_overrides, dump_spec, load_spec
    from .sweep_ota import format_metric
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import apply_overrides, dump_spec, load_spec
    from sweep_ota import format_metric


Metric = float | int | str | bool | None
Overrides = dict[str, Metric]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def rounded(value: float) -> float:
    return round(value, 6)


def override_strings(overrides: Overrides) -> list[str]:
    rendered: list[str] = []
    for key in sorted(overrides):
        value = overrides[key]
        if isinstance(value, float):
            raw = f"{value:.12g}"
        elif isinstance(value, bool):
            raw = "true" if value else "false"
        elif value is None:
            raw = "null"
        else:
            raw = str(value)
        rendered.append(f"{key}={raw}")
    return rendered


def override_cli_args(overrides: Overrides) -> list[str]:
    args: list[str] = []
    for item in override_strings(overrides):
        args.extend(["--set", item])
    return args


def unique_candidates(candidates: list[Overrides]) -> list[Overrides]:
    seen: set[tuple[str, ...]] = set()
    unique: list[Overrides] = []
    for candidate in candidates:
        key = tuple(override_strings(candidate))
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def generated_candidates(spec: dict[str, Any], baseline: dict[str, Any] | None = None) -> list[Overrides]:
    devices = spec["devices"]
    mn_w = float(devices["mn_in"]["w_um"])
    mn_l = float(devices["mn_in"]["l_um"])
    mp_l = float(devices["mp_load"]["l_um"])
    bias = float(spec["bias_tail_v"])
    misses = missed_metrics(baseline) if baseline else {"dc_gain_db", "unity_gain_hz"}

    candidates: list[Overrides] = []
    if {"dc_gain_db", "unity_gain_hz"} <= misses:
        candidates.extend(
            [
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.40, 1.50, 1.50, 0.02),
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.30, 1.50, 1.50, 0.04),
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.30, 1.50, 1.50, 0.00),
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.85, 1.50, 1.50, 0.01),
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.20, 1.20, 1.20, 0.04),
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.30, 1.10, 1.10, 0.08),
            ]
        )
    if "dc_gain_db" in misses:
        candidates.extend(
            [
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.00, 1.20, 1.20, 0.00),
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.15, 1.40, 1.40, 0.00),
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.30, 1.50, 1.70, 0.02),
            ]
        )
    if "unity_gain_hz" in misses:
        candidates.extend(
            [
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.20, 1.00, 1.00, 0.04),
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.40, 1.00, 1.00, 0.06),
                balanced_candidate(mn_w, mn_l, mp_l, bias, 1.60, 1.10, 1.10, 0.08),
            ]
        )
    if not candidates:
        candidates.append(balanced_candidate(mn_w, mn_l, mp_l, bias, 1.0, 1.0, 1.0, 0.0))
    return unique_candidates(candidates)


def balanced_candidate(
    mn_w: float,
    mn_l: float,
    mp_l: float,
    bias: float,
    w_factor: float,
    mn_l_factor: float,
    mp_l_factor: float,
    bias_delta: float,
) -> Overrides:
    return {
        "bias_tail_v": rounded(clamp(bias + bias_delta, 0.25, 1.2)),
        "devices.mn_in.w_um": rounded(mn_w * w_factor),
        "devices.mn_in.l_um": rounded(mn_l * mn_l_factor),
        "devices.mp_load.l_um": rounded(mp_l * mp_l_factor),
    }


def missed_metrics(evaluation: dict[str, Any] | None) -> set[str]:
    metrics: set[str] = set()
    if not evaluation:
        return metrics
    for result in evaluation.get("results", []):
        score = result.get("score", {})
        for metric in score.get("misses", {}):
            metrics.add(metric)
    return metrics


def load_evaluation(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_evaluation(
    spec_path: str,
    template_path: str,
    out_dir: Path,
    overrides: Overrides,
    dry_run: bool,
) -> dict[str, Any]:
    evaluator = Path(__file__).resolve().parent / "evaluate_ota.py"
    cmd = [
        sys.executable,
        str(evaluator),
        "--spec",
        spec_path,
        "--template",
        template_path,
        "--out-dir",
        str(out_dir),
    ]
    cmd.extend(override_cli_args(overrides))
    if dry_run:
        cmd.append("--dry-run")

    completed = subprocess.run(cmd)
    evaluation_path = out_dir / "evaluation.json"
    evaluation = load_evaluation(evaluation_path) if evaluation_path.exists() else {"summary": {}, "results": []}
    return {
        "returncode": completed.returncode,
        "command": cmd,
        "evaluation_path": str(evaluation_path),
        "evaluation": evaluation,
    }


def score_evaluation(evaluation: dict[str, Any]) -> dict[str, Any]:
    summary = evaluation.get("summary", {})
    total_miss = 0.0
    worst_miss = 0.0
    power_sum = 0.0
    power_count = 0
    for result in evaluation.get("results", []):
        for miss in result.get("score", {}).get("misses", {}).values():
            miss_value = float(miss)
            if not math.isfinite(miss_value):
                miss_value = 1e6
            total_miss += miss_value
            worst_miss = max(worst_miss, miss_value)
        power = result.get("measures", {}).get("power_w")
        if isinstance(power, (int, float)) and math.isfinite(float(power)):
            power_sum += float(power)
            power_count += 1

    errored = int(summary.get("errored_count", 0) or 0)
    failed = int(summary.get("failed_count", 0) or 0)
    passed = int(summary.get("passed_count", 0) or 0)
    average_power = power_sum / power_count if power_count else None
    score = errored * 1e6 + failed * 10.0 + total_miss + worst_miss * 0.1
    if average_power is not None:
        score += average_power * 1e3
    score -= passed * 0.01
    return {
        "pass": bool(summary.get("pass", False)),
        "score": score,
        "total_miss": total_miss,
        "worst_miss": worst_miss,
        "average_power_w": average_power,
        "passed_count": passed,
        "failed_count": failed,
        "errored_count": errored,
    }


def rank_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        results,
        key=lambda item: (
            item["returncode"] != 0,
            not item["agent_score"]["pass"],
            item["agent_score"]["failed_count"],
            item["agent_score"]["score"],
        ),
    )


def write_report(path: Path, data: dict[str, Any]) -> None:
    baseline_score = data["baseline"]["agent_score"]
    ranked = data["ranked_candidates"]
    best = ranked[0] if ranked else None
    lines = [
        "# OTA Agent Loop",
        "",
        f"- Spec: `{data['spec']}`",
        f"- Template: `{data['template']}`",
        f"- Run root: `{data['out_dir']}`",
        f"- Applied best passing candidate: {'yes' if data['applied'] else 'no'}",
        "",
        "## Baseline",
        "",
        f"- Pass: `{baseline_score['pass']}`",
        f"- Passed cases: `{baseline_score['passed_count']}`",
        f"- Failed cases: `{baseline_score['failed_count']}`",
        f"- Total normalized miss: `{format_metric(baseline_score['total_miss'])}`",
        "",
        "## Ranked Candidates",
        "",
        "| Rank | Pass | Passed | Failed | Total Miss | Worst Miss | Avg Power W | Overrides |",
        "| ---: | :---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for rank, candidate in enumerate(ranked[:20], start=1):
        score = candidate["agent_score"]
        lines.append(
            "| {rank} | {passed} | {passed_count} | {failed_count} | {total_miss} | {worst_miss} | {power} | `{overrides}` |".format(
                rank=rank,
                passed="yes" if score["pass"] else "no",
                passed_count=score["passed_count"],
                failed_count=score["failed_count"],
                total_miss=format_metric(score["total_miss"]),
                worst_miss=format_metric(score["worst_miss"]),
                power=format_metric(score["average_power_w"]),
                overrides=", ".join(override_strings(candidate["overrides"])),
            )
        )

    lines.extend(["", "## Recommendation", ""])
    if best and best["agent_score"]["pass"]:
        if data["applied"]:
            lines.append("Best passing candidate was applied to the source spec. Run `make eval-ota-strict` next.")
        else:
            lines.append("A passing candidate exists. Review it, then rerun with `make agent-ota-apply` if acceptable.")
    elif best:
        lines.append(
            "No candidate passed every evaluation case. The best candidate improved the score; inspect the ranked table before broadening the search."
        )
        lines.append(
            "Next search axes: gm/ID characterization, separate input/load length sweeps, and topology alternatives if 5T OTA tradeoffs remain too tight."
        )
    else:
        lines.append("No candidates were evaluated.")

    lines.extend(
        [
            "",
            "## Recursive Loop Contract",
            "",
            "1. Run preflight checks.",
            "2. Evaluate baseline.",
            "3. Generate bounded candidates from actual target misses.",
            "4. Evaluate candidates with ngspice.",
            "5. Apply only a passing candidate unless explicitly overridden.",
            "6. Re-run `make check` and `make eval-ota-strict` after any applied sizing change.",
            "7. Commit and push each verified milestone.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--max-candidates", type=int, default=6)
    parser.add_argument("--apply-best", action="store_true")
    parser.add_argument("--plan-only", action="store_true", help="Generate candidates and report without running ngspice")
    args = parser.parse_args()

    spec = load_spec(args.spec)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_eval: dict[str, Any] | None = None
    if not args.plan_only:
        baseline_run = run_evaluation(args.spec, args.template, out_dir / "baseline", {}, dry_run=False)
        baseline_eval = baseline_run["evaluation"]
    else:
        baseline_run = {
            "returncode": 0,
            "command": [],
            "evaluation_path": "",
            "evaluation": {"summary": {"pass": False, "passed_count": 0, "failed_count": 0, "errored_count": 0}, "results": []},
        }

    candidates = generated_candidates(spec, baseline_eval)[: max(0, args.max_candidates)]
    candidate_results: list[dict[str, Any]] = []
    for index, overrides in enumerate(candidates, start=1):
        if args.plan_only:
            evaluation = {"summary": {"pass": False, "passed_count": 0, "failed_count": 0, "errored_count": 0}, "results": []}
            run = {"returncode": 0, "command": [], "evaluation_path": "", "evaluation": evaluation}
        else:
            run = run_evaluation(
                args.spec,
                args.template,
                out_dir / f"candidate_{index:03d}",
                overrides,
                dry_run=False,
            )
            evaluation = run["evaluation"]
        candidate_results.append(
            {
                "candidate": index,
                "overrides": overrides,
                "returncode": run["returncode"],
                "command": run["command"],
                "evaluation_path": run["evaluation_path"],
                "evaluation": evaluation,
                "agent_score": score_evaluation(evaluation),
            }
        )
        if run["returncode"] != 0:
            break

    ranked = rank_results(candidate_results)
    best = ranked[0] if ranked else None
    applied = False
    if args.apply_best and best and best["agent_score"]["pass"]:
        updated_spec = apply_overrides(load_spec(args.spec), override_strings(best["overrides"]))
        dump_spec(updated_spec, args.spec)
        applied = True

    data = {
        "spec": args.spec,
        "template": args.template,
        "out_dir": str(out_dir),
        "plan_only": args.plan_only,
        "applied": applied,
        "baseline": {
            "returncode": baseline_run["returncode"],
            "command": baseline_run["command"],
            "evaluation_path": baseline_run["evaluation_path"],
            "evaluation": baseline_run["evaluation"],
            "agent_score": score_evaluation(baseline_run["evaluation"]),
        },
        "candidates": candidate_results,
        "ranked_candidates": ranked,
    }
    json_path = out_dir / "agent_loop.json"
    json_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(Path(args.report), data)
    print(f"Wrote {json_path}")
    print(f"Wrote {args.report}")
    if best:
        print(json.dumps({"best": {"overrides": best["overrides"], "agent_score": best["agent_score"]}}, indent=2, sort_keys=True))
    if any(item["returncode"] != 0 for item in candidate_results) or baseline_run["returncode"] != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
