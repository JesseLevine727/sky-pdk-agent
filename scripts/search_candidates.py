#!/usr/bin/env python3
"""Run a spec-driven candidate search with optional post-layout signoff."""

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
    from .spec_io import apply_overrides, dump_spec, load_spec
    from .sweep_ota import format_metric
    from .tool_env import apply_local_tool_env
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import apply_overrides, dump_spec, load_spec
    from sweep_ota import format_metric
    from tool_env import apply_local_tool_env


Metric = float | int | str | bool | None


def render_value(value: Metric) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def override_strings(overrides: dict[str, Metric]) -> list[str]:
    return [f"{key}={render_value(overrides[key])}" for key in sorted(overrides)]


def axis_config(spec: dict[str, Any], profile: str) -> dict[str, list[Metric]]:
    search = spec.get("search", {})
    if not isinstance(search, dict):
        raise ValueError("spec has no search mapping")
    profiles = search.get("profiles", {})
    if isinstance(profiles, dict) and profile in profiles:
        selected = profiles[profile]
        if not isinstance(selected, dict):
            raise ValueError(f"search.profiles.{profile} must be a mapping")
        axes = selected.get("axes", {})
    else:
        axes = search.get("axes", {})
    if not isinstance(axes, dict) or not axes:
        raise ValueError(f"search profile {profile!r} has no axes")
    parsed: dict[str, list[Metric]] = {}
    for key, values in axes.items():
        if not isinstance(values, list) or not values:
            raise ValueError(f"search axis {key!r} must be a non-empty list")
        parsed[str(key)] = values
    return parsed


def candidate_overrides(spec: dict[str, Any], profile: str, max_candidates: int | None = None) -> list[dict[str, Metric]]:
    axes = axis_config(spec, profile)
    keys = list(axes)
    candidates = [dict(zip(keys, values)) for values in itertools.product(*(axes[key] for key in keys))]
    unique: list[dict[str, Metric]] = []
    seen: set[tuple[str, ...]] = set()
    for candidate in candidates:
        key = tuple(override_strings(candidate))
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique[:max_candidates] if max_candidates else unique


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def score_evaluation(evaluation: dict[str, Any]) -> dict[str, Any]:
    summary = evaluation.get("summary", {})
    total_miss = 0.0
    worst_miss = 0.0
    power_sum = 0.0
    power_count = 0
    for result in evaluation.get("results", []):
        misses = result.get("score", {}).get("misses", {})
        if isinstance(misses, dict):
            for miss in misses.values():
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
    score = errored * 1e6 + failed * 10 + total_miss + worst_miss * 0.1 - passed * 0.01
    if average_power is not None:
        score += average_power * 1e3
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


def run_schematic_eval(
    spec_path: Path,
    template: Path,
    out_dir: Path,
    report: Path,
    overrides: dict[str, Metric],
    dry_run: bool,
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "scripts/evaluate_ota.py",
        "--spec",
        str(spec_path),
        "--template",
        str(template),
        "--out-dir",
        str(out_dir),
        "--report",
        str(report),
    ]
    for override in override_strings(overrides):
        cmd.extend(["--set", override])
    if dry_run:
        cmd.append("--dry-run")
    completed = subprocess.run(cmd)
    evaluation = load_json(out_dir / "evaluation.json")
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "evaluation": evaluation,
        "score": score_evaluation(evaluation) if evaluation else {},
    }


def candidate_spec(base_spec: dict[str, Any], overrides: dict[str, Metric], candidate_dir: Path) -> Path:
    spec = apply_overrides(base_spec, override_strings(overrides))
    cell = str(spec.get("design", "block"))
    schematic = spec.setdefault("schematic", {})
    layout = spec.setdefault("layout", {})
    flow = spec.setdefault("flow", {})
    schematic["cell_netlist"] = str(candidate_dir / "schematic" / f"{cell}.spice")
    layout["magic_dir"] = str(candidate_dir / "layout" / "magic")
    layout["extracted_netlist"] = str(candidate_dir / "layout" / "extracted" / f"{cell}_extracted.spice")
    layout["lvs_extracted_netlist"] = str(candidate_dir / "layout" / "extracted" / f"{cell}_lvs.spice")
    flow["reports_dir"] = str(candidate_dir / "reports")
    flow["sim_root"] = str(candidate_dir / "sim" / "runs")
    flow["schematic_report"] = str(candidate_dir / "reports" / "latest_eval.md")
    flow["postlayout_report"] = str(candidate_dir / "reports" / "postlayout_eval.md")
    flow["drc_report_dir"] = str(candidate_dir / "reports" / "drc")
    flow["lvs_report"] = str(candidate_dir / "reports" / f"lvs_{cell}.md")
    path = candidate_dir / "effective_spec.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_spec(spec, path)
    return path


def run_postlayout_signoff(base_spec: dict[str, Any], overrides: dict[str, Metric], candidate_dir: Path, dry_run: bool) -> dict[str, Any]:
    spec_path = candidate_spec(base_spec, overrides, candidate_dir)
    cmd = [
        sys.executable,
        "scripts/signoff_block.py",
        "--spec",
        str(spec_path),
        "--report",
        str(candidate_dir / "reports" / "signoff_summary.md"),
        "--json",
        str(candidate_dir / "reports" / "signoff_summary.json"),
    ]
    if dry_run:
        cmd.append("--dry-run")
    completed = subprocess.run(cmd)
    summary = load_json(candidate_dir / "reports" / "signoff_summary.json")
    postlayout = load_json(candidate_dir / "sim" / "runs" / "signoff_postlayout_eval" / "evaluation.json")
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "summary": summary,
        "postlayout_evaluation": postlayout,
        "postlayout_score": score_evaluation(postlayout) if postlayout else {},
        "effective_spec": str(spec_path),
    }


def rank_key(result: dict[str, Any]) -> tuple[bool, int, float]:
    score = result.get("schematic", {}).get("score", {})
    return (
        not bool(score.get("pass", False)),
        int(score.get("failed_count", 999)),
        float(score.get("score", math.inf)),
    )


def final_rank_key(result: dict[str, Any]) -> tuple[int, bool, int, float]:
    postlayout = result.get("postlayout")
    if isinstance(postlayout, dict) and postlayout:
        score = postlayout.get("postlayout_score", {})
        return (
            0,
            not bool(score.get("pass", False)),
            int(score.get("failed_count", 999)),
            float(score.get("score", math.inf)),
        )
    schematic = result.get("schematic", {}).get("score", {})
    return (
        1,
        not bool(schematic.get("pass", False)),
        int(schematic.get("failed_count", 999)),
        float(schematic.get("score", math.inf)),
    )


def write_report(path: Path, results: list[dict[str, Any]], postlayout_top: int) -> None:
    lines = [
        "# Candidate Search",
        "",
        f"- Candidates: `{len(results)}`",
        f"- Post-layout candidates: `{postlayout_top}`",
        "",
        "| Rank | Schematic | Postlayout | Schematic Score | Postlayout Score | Avg Power W | Overrides |",
        "| ---: | :---: | :---: | ---: | ---: | ---: | --- |",
    ]
    for rank, result in enumerate(results[:30], start=1):
        schematic_score = result.get("schematic", {}).get("score", {})
        post = result.get("postlayout", {})
        post_score = post.get("postlayout_score", {}) if isinstance(post, dict) else {}
        post_status = ""
        if post:
            post_status = "yes" if post_score.get("pass") else "no"
        lines.append(
            "| {rank} | {schematic} | {post} | {schematic_score} | {post_score} | {power} | `{overrides}` |".format(
                rank=rank,
                schematic="yes" if schematic_score.get("pass") else "no",
                post=post_status,
                schematic_score=format_metric(schematic_score.get("score")),
                post_score=format_metric(post_score.get("score")),
                power=format_metric(schematic_score.get("average_power_w")),
                overrides=", ".join(override_strings(result["overrides"])),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--template")
    parser.add_argument("--profile", default="quick")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--report")
    parser.add_argument("--max-candidates", type=int)
    parser.add_argument("--postlayout-top", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply_local_tool_env()

    spec_path = Path(args.spec)
    spec = load_spec(spec_path)
    template = Path(args.template or spec.get("flow", {}).get("schematic_template", "circuits/ota/testbenches/ota_ac.spice.in"))
    out_root = Path(args.out_dir)
    report = Path(args.report) if args.report else out_root / "summary.md"
    candidates = candidate_overrides(spec, args.profile, args.max_candidates)

    results: list[dict[str, Any]] = []
    for index, overrides in enumerate(candidates, start=1):
        candidate_dir = out_root / f"candidate_{index:03d}"
        schematic = run_schematic_eval(
            spec_path,
            template,
            candidate_dir / "schematic_eval",
            candidate_dir / "reports" / "schematic_eval.md",
            overrides,
            args.dry_run,
        )
        results.append({"candidate": index, "overrides": overrides, "candidate_dir": str(candidate_dir), "schematic": schematic})
        if schematic["returncode"] != 0:
            break

    ranked = sorted(results, key=rank_key)
    for result in ranked[: max(0, args.postlayout_top)]:
        result["postlayout"] = run_postlayout_signoff(spec, result["overrides"], Path(result["candidate_dir"]) / "postlayout", args.dry_run)
    if args.postlayout_top:
        ranked = sorted(ranked, key=final_rank_key)

    manifest = {"spec": str(spec_path), "profile": args.profile, "results": ranked}
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "ranked_results.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(report, ranked, args.postlayout_top)
    print(f"Wrote {out_root / 'ranked_results.json'}")
    print(f"Wrote {report}")
    best = ranked[0] if ranked else None
    if best:
        postlayout = best.get("postlayout", {})
        print(
            json.dumps(
                {
                    "best_overrides": override_strings(best["overrides"]),
                    "schematic_pass": best["schematic"].get("score", {}).get("pass"),
                    "postlayout_pass": postlayout.get("postlayout_score", {}).get("pass") if isinstance(postlayout, dict) else None,
                },
                indent=2,
            )
        )
    return 0 if all(item["schematic"]["returncode"] == 0 for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
