#!/usr/bin/env python3
"""Turn a design intent YAML file into a deterministic scaffold plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only without PyYAML
    raise SystemExit("PyYAML is required. Run: python3 -m pip install -r requirements.txt") from exc


REQUIRED_TOP_LEVEL = ["design", "intent", "topology", "blocks", "files", "acceptance"]


def load_intent(path: str | Path) -> dict[str, Any]:
    intent_path = Path(path)
    data = yaml.safe_load(intent_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{intent_path} must contain a mapping")
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in data]
    if missing:
        raise ValueError(f"{intent_path} is missing required keys: {', '.join(missing)}")
    data["_meta"] = {"intent_path": str(intent_path)}
    return data


def _as_list(value: Any, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def _path_entries(files: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for category in sorted(files):
        for entry in _as_list(files[category], f"files.{category}"):
            if not isinstance(entry, str):
                raise ValueError(f"files.{category} entries must be strings")
            paths.append(entry)
    return paths


def build_plan(intent: dict[str, Any]) -> dict[str, Any]:
    files = intent.get("files", {})
    if not isinstance(files, dict):
        raise ValueError("files must be a mapping")
    blocks = _as_list(intent.get("blocks"), "blocks")
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise ValueError(f"blocks[{index}] must be a mapping")
        for key in ["name", "kind"]:
            if key not in block:
                raise ValueError(f"blocks[{index}] is missing {key}")

    acceptance = intent.get("acceptance", {})
    if not isinstance(acceptance, dict):
        raise ValueError("acceptance must be a mapping")
    commands = _as_list(acceptance.get("commands"), "acceptance.commands")
    checks = _as_list(acceptance.get("checks"), "acceptance.checks")

    return {
        "schema": "sky-pdk-agent.design_plan.v1",
        "design": intent["design"],
        "intent_path": intent.get("_meta", {}).get("intent_path", "unknown"),
        "intent": intent["intent"],
        "topology": intent["topology"],
        "blocks": blocks,
        "interfaces": _as_list(intent.get("interfaces"), "interfaces"),
        "requirements": intent.get("requirements", {}),
        "files": files,
        "planned_paths": _path_entries(files),
        "acceptance": {
            "commands": commands,
            "checks": checks,
        },
        "agent_loop": _as_list(intent.get("agent_loop"), "agent_loop"),
    }


def write_markdown_report(plan: dict[str, Any], path: str | Path) -> Path:
    report_path = Path(path)
    lines = [
        "# Design Intake Plan",
        "",
        f"- Design: `{plan['design']}`",
        f"- Intent source: `{plan['intent_path']}`",
        f"- Topology: `{plan['topology']}`",
        "",
        "## Intent",
        "",
        str(plan["intent"]).strip(),
        "",
        "## Blocks",
        "",
        "| Block | Kind | Role |",
        "| --- | --- | --- |",
    ]
    for block in plan["blocks"]:
        lines.append(
            f"| `{block['name']}` | `{block['kind']}` | {block.get('role', '')} |"
        )
    if plan["interfaces"]:
        lines.extend(["", "## Interfaces", ""])
        for interface in plan["interfaces"]:
            if isinstance(interface, dict):
                source = interface.get("from", "")
                target = interface.get("to", "")
                note = interface.get("note", "")
                lines.append(f"- `{source}` -> `{target}`: {note}")
            else:
                lines.append(f"- {interface}")
    lines.extend(["", "## Planned Files", ""])
    for planned_path in plan["planned_paths"]:
        lines.append(f"- `{planned_path}`")
    lines.extend(["", "## Acceptance Commands", ""])
    for command in plan["acceptance"]["commands"]:
        lines.append(f"- `{command}`")
    if plan["acceptance"]["checks"]:
        lines.extend(["", "## Acceptance Checks", ""])
        for check in plan["acceptance"]["checks"]:
            lines.append(f"- {check}")
    if plan["agent_loop"]:
        lines.extend(["", "## Agent Loop", ""])
        for step in plan["agent_loop"]:
            lines.append(f"- {step}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def scaffold_directories(plan: dict[str, Any], root: Path) -> list[Path]:
    created: list[Path] = []
    for planned_path in plan["planned_paths"]:
        path = root / planned_path
        directory = path if planned_path.endswith("/") else path.parent
        directory.mkdir(parents=True, exist_ok=True)
        keep = directory / ".gitkeep"
        if not keep.exists() and not any(directory.iterdir()):
            keep.write_text("", encoding="utf-8")
            created.append(keep)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", required=True, help="Design intent YAML file")
    parser.add_argument("--report", required=True, help="Markdown plan output")
    parser.add_argument("--json", help="Optional JSON plan output")
    parser.add_argument("--scaffold", action="store_true", help="Create planned directories")
    args = parser.parse_args()

    intent = load_intent(args.intent)
    plan = build_plan(intent)
    report_path = write_markdown_report(plan, args.report)
    print(f"Wrote {report_path}")
    if args.json:
        json_path = Path(args.json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote {json_path}")
    if args.scaffold:
        created = scaffold_directories(plan, Path.cwd())
        for path in created:
            print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
