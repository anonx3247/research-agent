from __future__ import annotations

from pathlib import Path

import yaml

from research_agent.config import load_config
from research_agent.runtime_config import write_runtime_config


def test_runtime_config_pins_worker_and_flat_delegation(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source.yaml"
    source.write_text(
        "model:\n  provider: tinfoil\n  default: kimi\ndelegation:\n  max_iterations: 50\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_CONFIG", str(source))
    config = load_config()
    destination = tmp_path / "runtime.yaml"

    write_runtime_config(
        destination,
        config.routes["open"].worker,
        config.settings,
        worker_count=3,
    )

    value = yaml.safe_load(destination.read_text(encoding="utf-8"))
    delegation = value["delegation"]
    assert value["model"]["provider"] == "tinfoil"
    assert delegation["provider"] == "openrouter"
    assert delegation["model"] == "deepseek/deepseek-v4-flash-0731"
    assert delegation["max_concurrent_children"] == 3
    assert delegation["max_spawn_depth"] == 1
    assert delegation["orchestrator_enabled"] is False
    assert value["max_iterations"] == 20
