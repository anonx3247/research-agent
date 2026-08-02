from __future__ import annotations

import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path

from .contracts import InvocationResult, ModelSpec, Usage


class HermesInvocationError(RuntimeError):
    """Raised when a Hermes one-shot process fails."""

    def __init__(self, message: str, usage: Usage | None = None) -> None:
        super().__init__(message)
        self.usage = usage or Usage()


class HermesRunner:
    def __init__(self, command: str = "hermes", timeout_seconds: int = 3600) -> None:
        self.command = command
        self.timeout_seconds = timeout_seconds

    def invoke(
        self,
        prompt: str,
        model: ModelSpec,
        usage_path: Path,
        extra_env: dict[str, str] | None = None,
    ) -> InvocationResult:
        command = [
            self.command,
            "--oneshot",
            prompt,
            "--provider",
            model.provider,
            "--model",
            model.model,
            "--usage-file",
            str(usage_path),
        ]
        if model.toolsets:
            command.extend(["--toolsets", ",".join(model.toolsets)])

        environment = os.environ.copy()
        environment.update(extra_env or {})
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=self.timeout_seconds,
            check=False,
            env=environment,
        )
        usage = self._read_usage(usage_path)
        if usage.estimated_cost_usd == 0.0 and (usage.input_tokens or usage.output_tokens):
            estimated_cost = (
                usage.input_tokens * model.input_price / 1_000_000
                + usage.output_tokens * model.output_price / 1_000_000
            )
            usage = replace(usage, estimated_cost_usd=estimated_cost)
        if completed.returncode != 0:
            diagnostic = completed.stderr.strip() or completed.stdout.strip()
            raise HermesInvocationError(
                f"Hermes {model.provider}/{model.model} failed: {diagnostic[-4000:]}",
                usage=usage,
            )
        if not completed.stdout.strip():
            raise HermesInvocationError(
                f"Hermes {model.provider}/{model.model} returned an empty response",
                usage=usage,
            )
        return InvocationResult(text=completed.stdout.strip(), usage=usage)

    @staticmethod
    def _read_usage(path: Path) -> Usage:
        if not path.exists():
            return Usage()
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return Usage()
        return Usage.from_dict(value if isinstance(value, dict) else {})
