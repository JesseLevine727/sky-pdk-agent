#!/usr/bin/env python3
"""Run a reusable file-based analog signoff plan from a block spec."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .spec_io import apply_overrides, dump_spec, load_spec
    from .tool_env import apply_local_tool_env
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import apply_overrides, dump_spec, load_spec
    from tool_env import apply_local_tool_env


ALL_STAGES = [
    "schematic",
    "schematic-eval",
    "layout",
    "drc",
    "extract-lvs",
    "lvs",
    "pex",
    "postlayout-eval",
]


@dataclass(frozen=True)
class Stage:
    name: str
    command: list[str]
    evidence: list[Path]


def repo_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else path


def mapping(spec: dict[str, Any], key: str) -> dict[str, Any]:
    value = spec.get(key, {})
    return value if isinstance(value, dict) else {}


def design_name(spec: dict[str, Any]) -> str:
    return str(spec.get("design") or mapping(spec, "schematic").get("cell_name") or "block")


def block_root(spec: dict[str, Any]) -> Path:
    schematic_netlist = mapping(spec, "schematic").get("cell_netlist")
    if schematic_netlist:
        parts = repo_path(str(schematic_netlist)).parts
        if "circuits" in parts:
            index = parts.index("circuits")
            if len(parts) > index + 1:
                return Path(*parts[: index + 2])
    return Path("circuits") / design_name(spec)


def paths_for(spec_path: Path, spec: dict[str, Any]) -> dict[str, Path | str]:
    flow = mapping(spec, "flow")
    schematic = mapping(spec, "schematic")
    layout = mapping(spec, "layout")
    root = block_root(spec)
    reports = repo_path(str(flow.get("reports_dir", root / "reports")))
    sim_root = repo_path(str(flow.get("sim_root", root / "sim" / "runs")))
    cell = str(layout.get("cell_name") or schematic.get("cell_name") or design_name(spec))
    magic_dir = repo_path(str(layout.get("magic_dir", root / "layout" / "magic")))
    extracted = repo_path(str(layout.get("extracted_netlist", root / "layout" / "extracted" / f"{cell}_extracted.spice")))
    lvs_extracted = repo_path(str(layout.get("lvs_extracted_netlist", extracted.with_name(f"{cell}_lvs.spice"))))
    return {
        "spec": spec_path,
        "cell": cell,
        "schematic_generator": repo_path(str(flow.get("schematic_generator", "scripts/render_ota_cell.py"))),
        "layout_generator": repo_path(str(flow.get("layout_generator", "scripts/generate_ota_magic_layout.py"))),
        "evaluator": repo_path(str(flow.get("evaluator", "scripts/evaluate_ota.py"))),
        "schematic_template": repo_path(str(flow.get("schematic_template", root / "testbenches" / "ota_ac.spice.in"))),
        "postlayout_template": repo_path(str(flow.get("postlayout_template", root / "testbenches" / "ota_ac_postlayout.spice.in"))),
        "schematic_netlist": repo_path(str(schematic.get("cell_netlist", root / "schematic" / f"{cell}.spice"))),
        "magic_dir": magic_dir,
        "layout_mag": magic_dir / f"{cell}.mag",
        "extracted": extracted,
        "lvs_extracted": lvs_extracted,
        "reports": reports,
        "drc_dir": repo_path(str(flow.get("drc_report_dir", reports / "drc"))),
        "lvs_report": repo_path(str(flow.get("lvs_report", reports / f"lvs_{cell}.md"))),
        "schematic_report": repo_path(str(flow.get("schematic_report", reports / "latest_eval.md"))),
        "postlayout_report": repo_path(str(flow.get("postlayout_report", reports / "postlayout_eval.md"))),
        "sim_root": sim_root,
    }


def selected_stages(raw: str) -> list[str]:
    if raw == "all":
        return ALL_STAGES
    requested = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(requested) - set(ALL_STAGES))
    if unknown:
        raise ValueError(f"unknown signoff stages: {', '.join(unknown)}")
    return [stage for stage in ALL_STAGES if stage in requested]


def build_plan(spec_path: Path, spec: dict[str, Any], stages: list[str]) -> list[Stage]:
    paths = paths_for(spec_path, spec)
    py = sys.executable
    plan: list[Stage] = []
    for stage in stages:
        if stage == "schematic":
            plan.append(Stage(stage, [py, str(paths["schematic_generator"]), "--spec", str(spec_path), "--out", str(paths["schematic_netlist"])], [paths["schematic_netlist"]]))  # type: ignore[list-item]
        elif stage == "schematic-eval":
            out_dir = Path(paths["sim_root"]) / "signoff_eval"
            plan.append(Stage(stage, [py, str(paths["evaluator"]), "--spec", str(spec_path), "--template", str(paths["schematic_template"]), "--out-dir", str(out_dir), "--report", str(paths["schematic_report"]), "--strict"], [paths["schematic_report"], out_dir / "evaluation.json"]))  # type: ignore[list-item]
        elif stage == "layout":
            plan.append(Stage(stage, [py, str(paths["layout_generator"]), "--spec", str(spec_path), "--out-dir", str(paths["magic_dir"]), "--run"], [paths["layout_mag"]]))  # type: ignore[list-item]
        elif stage == "drc":
            plan.append(Stage(stage, ["scripts/run_magic_drc.sh", str(paths["layout_mag"]), str(paths["drc_dir"])], [Path(paths["drc_dir"]) / "drc.md"]))  # type: ignore[arg-type]
        elif stage == "extract-lvs":
            plan.append(Stage(stage, ["scripts/run_magic_extract_lvs.sh", str(paths["layout_mag"]), str(paths["cell"]), str(paths["lvs_extracted"])], [paths["lvs_extracted"]]))  # type: ignore[list-item]
        elif stage == "lvs":
            plan.append(Stage(stage, ["scripts/run_netgen_lvs.sh", str(paths["lvs_extracted"]), str(paths["schematic_netlist"]), str(paths["cell"]), str(paths["lvs_report"])], [paths["lvs_report"]]))  # type: ignore[list-item]
        elif stage == "pex":
            plan.append(Stage(stage, ["scripts/run_magic_pex.sh", str(paths["layout_mag"]), str(paths["cell"]), str(paths["extracted"])], [paths["extracted"]]))  # type: ignore[list-item]
        elif stage == "postlayout-eval":
            out_dir = Path(paths["sim_root"]) / "signoff_postlayout_eval"
            plan.append(Stage(stage, [py, str(paths["evaluator"]), "--spec", str(spec_path), "--template", str(paths["postlayout_template"]), "--out-dir", str(out_dir), "--report", str(paths["postlayout_report"]), "--strict"], [paths["postlayout_report"], out_dir / "evaluation.json"]))  # type: ignore[list-item]
    return plan


def run_stage(stage: Stage, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"stage": stage.name, "command": stage.command, "returncode": 0}
    completed = subprocess.run(stage.command)
    return {"stage": stage.name, "command": stage.command, "returncode": completed.returncode}


def write_report(path: Path, spec_path: Path, plan: list[Stage], results: list[dict[str, Any]]) -> None:
    evidence = {stage.name: stage.evidence for stage in plan}
    passed = all(result["returncode"] == 0 for result in results)
    lines = [
        "# Block Signoff Summary",
        "",
        f"- Spec: `{spec_path}`",
        f"- Overall: {'PASS' if passed else 'FAIL'}",
        "",
        "| Stage | Result | Evidence | Command |",
        "| --- | :---: | --- | --- |",
    ]
    for result in results:
        stage_evidence = ", ".join(f"`{item}`" for item in evidence.get(result["stage"], []))
        lines.append(
            "| {stage} | {status} | {evidence} | `{command}` |".format(
                stage=result["stage"],
                status="pass" if result["returncode"] == 0 else "fail",
                evidence=stage_evidence,
                command=shlex.join(result["command"]),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def effective_spec_path(spec_path: Path, spec: dict[str, Any], overrides: list[str], out_dir: Path | None) -> Path:
    if not overrides:
        return spec_path
    if out_dir is None:
        raise ValueError("--out-dir is required when using --set overrides")
    out_dir.mkdir(parents=True, exist_ok=True)
    effective = apply_overrides(spec, overrides)
    path = out_dir / "effective_spec.yaml"
    dump_spec(effective, path)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--stages", default="all")
    parser.add_argument("--report")
    parser.add_argument("--json")
    parser.add_argument("--out-dir", help="Working directory for --set effective specs")
    parser.add_argument("--set", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply_local_tool_env()

    source_spec_path = Path(args.spec).expanduser()
    source_spec = load_spec(source_spec_path)
    work_dir = repo_path(args.out_dir) if args.out_dir else None
    spec_path = effective_spec_path(source_spec_path, source_spec, args.set, work_dir)
    spec = load_spec(spec_path)
    paths = paths_for(spec_path, spec)
    report_path = repo_path(args.report) if args.report else Path(paths["reports"]) / "signoff_summary.md"
    json_path = repo_path(args.json) if args.json else Path(paths["reports"]) / "signoff_summary.json"
    plan = build_plan(spec_path, spec, selected_stages(args.stages))

    results: list[dict[str, Any]] = []
    for stage in plan:
        result = run_stage(stage, args.dry_run)
        results.append(result)
        if result["returncode"] != 0:
            break
    passed = all(result["returncode"] == 0 for result in results)
    write_report(report_path, spec_path, plan, results)
    write_json(json_path, {"spec": str(spec_path), "pass": passed, "results": results})
    print(f"Wrote {report_path}")
    print(f"Wrote {json_path}")
    print(json.dumps({"pass": passed, "stage_count": len(results)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
