#!/usr/bin/env python3
"""Spec loading and flattening helpers for analog flow scripts."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only without PyYAML
    raise SystemExit("PyYAML is required. Run: python3 -m pip install -r requirements.txt") from exc


Scalar = str | int | float | bool | None


def load_spec(path: str | Path) -> dict[str, Any]:
    spec_path = Path(path)
    with spec_path.open("r", encoding="utf-8") as handle:
        if spec_path.suffix.lower() == ".json":
            data = json.load(handle)
        else:
            data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"{spec_path} must contain a mapping at the top level")

    data = expand_env(data)
    data["_meta"] = {"spec_path": str(spec_path)}
    return data


def dump_spec(spec: dict[str, Any], path: str | Path) -> None:
    clean = copy.deepcopy(spec)
    clean.pop("_meta", None)
    with Path(path).open("w", encoding="utf-8") as handle:
        yaml.safe_dump(clean, handle, sort_keys=False)


def expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: expand_env(item) for key, item in value.items()}
    return value


def parse_scalar(raw: str) -> Scalar:
    lowered = raw.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    try:
        if any(ch in lowered for ch in [".", "e"]):
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def apply_overrides(spec: dict[str, Any], overrides: list[str] | None) -> dict[str, Any]:
    updated = copy.deepcopy(spec)
    for override in overrides or []:
        if "=" not in override:
            raise ValueError(f"Override must be key.path=value, got {override!r}")
        dotted_path, raw_value = override.split("=", 1)
        set_by_path(updated, dotted_path, parse_scalar(raw_value))
    return updated


def set_by_path(data: dict[str, Any], dotted_path: str, value: Scalar) -> None:
    parts = [part for part in dotted_path.split(".") if part]
    if not parts:
        raise ValueError("Override path cannot be empty")
    cursor: dict[str, Any] = data
    for part in parts[:-1]:
        next_value = cursor.setdefault(part, {})
        if not isinstance(next_value, dict):
            raise ValueError(f"Cannot set {dotted_path}: {part} is not a mapping")
        cursor = next_value
    cursor[parts[-1]] = value


def flatten_for_template(spec: dict[str, Any]) -> dict[str, str]:
    params: dict[str, Any] = {}
    params["spec_path"] = spec.get("_meta", {}).get("spec_path", "unknown")

    for key in [
        "design",
        "pdk",
        "supply_v",
        "temperature_c",
        "load_cap_f",
        "common_mode_v",
        "bias_tail_v",
    ]:
        if key in spec:
            params[key] = spec[key]

    simulation = spec.get("simulation", {})
    if isinstance(simulation, dict):
        for key, value in simulation.items():
            params[key] = value

    devices = spec.get("devices", {})
    if isinstance(devices, dict):
        for device_name, device_values in devices.items():
            if not isinstance(device_values, dict):
                continue
            for key, value in device_values.items():
                params[f"{device_name}_{key}"] = value

    return {key: spice_literal(value) for key, value in params.items()}


def spice_literal(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    if isinstance(value, bool):
        return "1" if value else "0"
    if value is None:
        return ""
    return str(value)


def target_bounds(spec: dict[str, Any]) -> dict[str, dict[str, float]]:
    targets = spec.get("targets", {})
    if not isinstance(targets, dict):
        return {}
    bounds: dict[str, dict[str, float]] = {}
    for name, config in targets.items():
        if not isinstance(config, dict):
            continue
        parsed: dict[str, float] = {}
        for bound in ["min", "max"]:
            if bound in config:
                parsed[bound] = float(config[bound])
        bounds[name] = parsed
    return bounds

