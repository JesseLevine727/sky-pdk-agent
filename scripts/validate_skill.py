#!/usr/bin/env python3
"""Small repo-local validator for Codex skill metadata."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


NAME_RE = re.compile(r"^[a-z0-9-]{1,63}$")


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return [f"missing {skill_file}"]

    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return ["SKILL.md must start with YAML frontmatter"]

    try:
        _, frontmatter, body = text.split("---", 2)
    except ValueError:
        return ["SKILL.md frontmatter must be delimited by ---"]

    try:
        metadata = yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError as exc:
        return [f"invalid YAML frontmatter: {exc}"]

    name = metadata.get("name")
    description = metadata.get("description")
    if not isinstance(name, str) or not NAME_RE.match(name):
        errors.append("frontmatter name must be lowercase letters, digits, and hyphens")
    if not isinstance(description, str) or len(description.strip()) < 40:
        errors.append("frontmatter description must be a meaningful string")
    if not body.strip():
        errors.append("SKILL.md body cannot be empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir")
    args = parser.parse_args()

    errors = validate(Path(args.skill_dir))
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print(f"ok: {args.skill_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

