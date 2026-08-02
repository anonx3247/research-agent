from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .contracts import ModelSpec, Settings


def active_hermes_config() -> Path:
    explicit = os.environ.get("HERMES_CONFIG", "").strip()
    if explicit:
        return Path(explicit).expanduser()
    hermes_home = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
    return hermes_home / "config.yaml"


def write_runtime_config(
    destination: Path,
    worker: ModelSpec,
    settings: Settings,
    worker_count: int,
) -> None:
    source = active_hermes_config()
    if not source.is_file():
        raise FileNotFoundError(f"Hermes config not found: {source}")
    raw = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Hermes config must contain a YAML mapping: {source}")

    delegation: dict[str, Any] = dict(raw.get("delegation") or {})
    delegation.update(
        {
            "provider": worker.provider,
            "model": worker.model,
            "base_url": "",
            "api_key": "",
            "max_concurrent_children": worker_count,
            "max_spawn_depth": 1,
            "orchestrator_enabled": False,
            "max_iterations": 12,
            "child_timeout_seconds": settings.timeout_seconds,
            "max_summary_chars": 16_000,
        }
    )
    raw["delegation"] = delegation
    raw["max_iterations"] = settings.parent_max_iterations
    destination.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
