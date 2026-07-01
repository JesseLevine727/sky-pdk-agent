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


def load_catalog(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    catalog_path = Path(path)
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{catalog_path} must contain a mapping")
    templates = data.get("templates", {})
    if not isinstance(templates, dict):
        raise ValueError(f"{catalog_path} templates must be a mapping")
    data["_meta"] = {"catalog_path": str(catalog_path)}
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


def _template_summary(block: dict[str, Any], templates: dict[str, Any]) -> dict[str, Any]:
    kind = str(block.get("kind", ""))
    template = templates.get(kind)
    if not isinstance(template, dict):
        return {
            "block": block.get("name"),
            "kind": kind,
            "matched": False,
            "supports": {},
            "commands": {},
            "files": {},
            "notes": ["No supported template matched this block kind."],
        }
    return {
        "block": block.get("name"),
        "kind": kind,
        "matched": True,
        "template_name": template.get("name", kind),
        "description": template.get("description", ""),
        "supports": template.get("supports", {}),
        "commands": template.get("commands", {}),
        "files": template.get("files", {}),
        "specs": template.get("specs", []),
    }


def _template_matches(blocks: list[Any], catalog: dict[str, Any]) -> list[dict[str, Any]]:
    templates = catalog.get("templates", {})
    if not isinstance(templates, dict):
        templates = {}
    return [_template_summary(block, templates) for block in blocks if isinstance(block, dict)]


def build_plan(intent: dict[str, Any], catalog: dict[str, Any] | None = None) -> dict[str, Any]:
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

    catalog = catalog or {}
    template_matches = _template_matches(blocks, catalog)
    return {
        "schema": "sky-pdk-agent.design_plan.v1",
        "design": intent["design"],
        "intent_path": intent.get("_meta", {}).get("intent_path", "unknown"),
        "catalog_path": catalog.get("_meta", {}).get("catalog_path"),
        "intent": intent["intent"],
        "topology": intent["topology"],
        "blocks": blocks,
        "template_matches": template_matches,
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
    if plan.get("template_matches"):
        lines.extend(["", "## Template Coverage", ""])
        lines.append("| Block | Kind | Matched | Schematic | Layout | LVS/PEX | Post-layout |")
        lines.append("| --- | --- | :---: | :---: | :---: | :---: | :---: |")
        for match in plan["template_matches"]:
            supports = match.get("supports", {})
            lvs_pex = bool(supports.get("lvs")) and bool(supports.get("pex"))
            lines.append(
                "| `{block}` | `{kind}` | {matched} | {schematic} | {layout} | {lvs_pex} | {postlayout} |".format(
                    block=match.get("block", ""),
                    kind=match.get("kind", ""),
                    matched="yes" if match.get("matched") else "no",
                    schematic="yes" if supports.get("schematic_eval") else "no",
                    layout="yes" if supports.get("layout") else "no",
                    lvs_pex="yes" if lvs_pex else "no",
                    postlayout="yes" if supports.get("postlayout_eval") else "no",
                )
            )
        unmatched = [match for match in plan["template_matches"] if not match.get("matched")]
        if unmatched:
            lines.extend(["", "Unsupported block kinds require a new template before end-to-end claims."])
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
    parser.add_argument("--catalog", help="Supported analog block template catalog")
    parser.add_argument("--json", help="Optional JSON plan output")
    parser.add_argument("--scaffold", action="store_true", help="Create planned directories")
    args = parser.parse_args()

    intent = load_intent(args.intent)
    catalog = load_catalog(args.catalog)
    plan = build_plan(intent, catalog)
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
