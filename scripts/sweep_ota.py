#!/usr/bin/env python3
"""Run a small deterministic OTA sizing sweep through run_ngspice.py."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from .spec_io import load_spec
except ImportError:  # pragma: no cover - command-line script mode
    from spec_io import load_spec


def candidate_overrides(spec_path: str) -> list[list[str]]:
    spec = load_spec(spec_path)
    mn_in_w = float(spec["devices"]["mn_in"]["w_um"])
    tail_bias = float(spec["bias_tail_v"])
    candidates: list[list[str]] = []
    for w_scale in [0.85, 1.0, 1.2]:
        for bias_delta in [-0.05, 0.0, 0.05]:
            candidates.append(
                [
                    f"devices.mn_in.w_um={mn_in_w * w_scale:.6g}",
                    f"bias_tail_v={tail_bias + bias_delta:.6g}",
                ]
            )
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    runner = script_dir / "run_ngspice.py"
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []
    for index, overrides in enumerate(candidate_overrides(args.spec), start=1):
        run_dir = out_root / f"candidate_{index:02d}"
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
        manifest.append(
            {
                "candidate": index,
                "overrides": overrides,
                "run_dir": str(run_dir),
                "returncode": completed.returncode,
            }
        )
        if completed.returncode != 0:
            break

    manifest_path = out_root / "sweep_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path}")
    return 0 if all(item["returncode"] == 0 for item in manifest) else 1


if __name__ == "__main__":
    raise SystemExit(main())
