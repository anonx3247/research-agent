from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from research_agent.contracts import ModelSpec
from research_agent.hermes import HermesRunner


def test_estimates_cost_when_provider_reports_tokens_only(tmp_path: Path) -> None:
    usage_path = tmp_path / "usage.json"
    model = ModelSpec(
        provider="private-provider",
        model="worker",
        input_price=1.0,
        output_price=2.0,
    )

    captured_env: dict[str, str] = {}

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured_env.update(kwargs["env"])
        usage_path.write_text(
            json.dumps({"input_tokens": 1_000_000, "output_tokens": 500_000}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="OK", stderr="")

    with patch("research_agent.hermes.subprocess.run", side_effect=fake_run):
        result = HermesRunner().invoke(
            "prompt",
            model,
            usage_path,
            extra_env={"HERMES_CONFIG": "/tmp/runtime.yaml"},
        )

    assert result.usage.estimated_cost_usd == 2.0
    assert captured_env["HERMES_CONFIG"] == "/tmp/runtime.yaml"
