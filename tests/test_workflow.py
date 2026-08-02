from __future__ import annotations

from pathlib import Path

import yaml

from research_agent.config import load_config
from research_agent.contracts import InvocationResult, ModelSpec, Usage
from research_agent.workflow import ResearchWorkflow


class FakeRunner:
    def __init__(self) -> None:
        self.prompt = ""
        self.model: ModelSpec | None = None
        self.runtime_config: dict = {}

    def invoke(
        self,
        prompt: str,
        model: ModelSpec,
        usage_path: Path,
        extra_env: dict[str, str] | None = None,
    ) -> InvocationResult:
        self.prompt = prompt
        self.model = model
        config_path = Path((extra_env or {})["HERMES_CONFIG"])
        self.runtime_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return InvocationResult("# Report", Usage(estimated_cost_usd=0.05))


def test_open_workflow_uses_one_parent_and_native_delegation_config(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "hermes.yaml"
    source.write_text("model: {provider: tinfoil, default: kimi}\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_CONFIG", str(source))
    config = load_config()
    runner = FakeRunner()

    result = ResearchWorkflow(config, runner).run(
        "Public question",
        config.routes["open"],
        worker_count=3,
    )

    assert result.text == "# Report"
    assert runner.model == config.routes["open"].planner
    assert "Call `delegate_task` once" in runner.prompt
    assert "public web sources only" in runner.prompt
    delegation = runner.runtime_config["delegation"]
    assert delegation["provider"] == "openrouter"
    assert delegation["model"] == "deepseek/deepseek-v4-flash-0731"


def test_private_workflow_includes_library_and_tinfoil_workers(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "hermes.yaml"
    source.write_text("model: {provider: tinfoil, default: kimi}\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_CONFIG", str(source))
    config = load_config()
    runner = FakeRunner()

    ResearchWorkflow(config, runner).run(
        "Private question",
        config.routes["private"],
        worker_count=2,
    )

    assert "~/dev/library" in runner.prompt
    delegation = runner.runtime_config["delegation"]
    assert delegation["provider"] == "tinfoil"
    assert delegation["model"] == "gpt-oss-120b"
