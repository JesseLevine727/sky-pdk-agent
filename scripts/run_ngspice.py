#!/usr/bin/env python3
"""Render a SPICE template, run ngspice, and parse measurements."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from string import Template

try:
    from .parse_measures import parse_measure_file
    from .spec_io import apply_overrides, dump_spec, flatten_for_template, load_spec
    from .tool_env import apply_local_tool_env
except ImportError:  # pragma: no cover - command-line script mode
    from parse_measures import parse_measure_file
    from spec_io import apply_overrides, dump_spec, flatten_for_template, load_spec
    from tool_env import apply_local_tool_env


def render_template(template_path: Path, params: dict[str, str]) -> str:
    template = Template(template_path.read_text(encoding="utf-8"))
    rendered = template.safe_substitute(params)
    if "${" in rendered:
        missing = sorted({chunk.split("}", 1)[0] for chunk in rendered.split("${")[1:]})
        raise ValueError(f"Unresolved template variables in {template_path}: {missing}")
    return rendered


def default_out_dir(template_path: Path) -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return template_path.parents[1] / "sim" / "runs" / stamp


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="YAML or JSON spec")
    parser.add_argument("--template", required=True, help="SPICE template path")
    parser.add_argument("--out-dir", help="Run output directory")
    parser.add_argument("--set", action="append", default=[], help="Override, e.g. devices.mn_in.w_um=16")
    parser.add_argument("--dry-run", action="store_true", help="Render netlist only")
    parser.add_argument("--ngspice", default="ngspice", help="ngspice executable")
    args = parser.parse_args()
    apply_local_tool_env()

    spec_path = Path(args.spec)
    template_path = Path(args.template)
    out_dir = Path(args.out_dir) if args.out_dir else default_out_dir(template_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    spec = apply_overrides(load_spec(spec_path), args.set)
    params = flatten_for_template(spec)
    rendered = render_template(template_path, params)

    netlist_path = out_dir / "rendered.spice"
    effective_spec_path = out_dir / "effective_spec.yaml"
    context_path = out_dir / "template_context.json"
    spiceinit_path = out_dir / ".spiceinit"
    netlist_path.write_text(rendered, encoding="utf-8")
    dump_spec(spec, effective_spec_path)
    context_path.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pdk_spiceinit = Path(str(params.get("model_lib", ""))).parent / "spinit"
    if pdk_spiceinit.exists():
        shutil.copyfile(pdk_spiceinit, spiceinit_path)

    if args.dry_run:
        print(f"Rendered {netlist_path}")
        return 0

    if not shutil.which(args.ngspice):
        print(
            f"ngspice executable not found: {args.ngspice}. "
            "Install ngspice or rerun with --dry-run.",
            file=sys.stderr,
        )
        return 127

    log_path = out_dir / "ngspice.log"
    cmd = [args.ngspice, "-b", "-o", "ngspice.log", "rendered.spice"]
    completed = subprocess.run(cmd, cwd=out_dir, text=True)
    if completed.returncode != 0:
        print(f"ngspice failed with exit code {completed.returncode}. Log: {log_path}", file=sys.stderr)
        return completed.returncode

    measures = parse_measure_file(log_path)
    measures_path = out_dir / "measures.json"
    measures_path.write_text(json.dumps(measures, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {measures_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
