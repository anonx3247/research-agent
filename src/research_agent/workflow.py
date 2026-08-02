from __future__ import annotations

import tempfile
from pathlib import Path

from .contracts import AppConfig, InvocationResult, Route
from .hermes import HermesRunner
from .prompts import render_prompt
from .runtime_config import write_runtime_config


class ResearchWorkflow:
    def __init__(self, config: AppConfig, runner: HermesRunner) -> None:
        self.config = config
        self.runner = runner

    def run(self, question: str, route: Route, worker_count: int) -> InvocationResult:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("research question cannot be empty")
        if not 1 <= worker_count <= self.config.settings.max_workers:
            raise ValueError(f"workers must be between 1 and {self.config.settings.max_workers}")

        mode_rules, worker_mode_rules = self._mode_rules(route.name)
        prompt = render_prompt(
            "workflow",
            {
                "QUESTION": clean_question,
                "MODE": route.name,
                "WORKER_COUNT": str(worker_count),
                "WORKER_PROVIDER": route.worker.provider,
                "WORKER_MODEL": route.worker.model,
                "MODE_RULES": mode_rules,
                "WORKER_MODE_RULES": worker_mode_rules,
            },
        )

        with tempfile.TemporaryDirectory(prefix="research-agent-") as temporary:
            temp_dir = Path(temporary)
            runtime_config = temp_dir / "hermes-config.yaml"
            usage_path = temp_dir / "usage.json"
            write_runtime_config(
                runtime_config,
                route.worker,
                self.config.settings,
                worker_count,
            )
            return self.runner.invoke(
                prompt,
                route.planner,
                usage_path,
                extra_env={"HERMES_CONFIG": str(runtime_config)},
            )

    @staticmethod
    def _mode_rules(mode: str) -> tuple[str, str]:
        if mode == "private":
            return (
                "Every parent and child model call must use Tinfoil. Local and private "
                "sources are allowed.",
                "When relevant, search the local library with `cd ~/dev/library && uv run "
                "library-search QUERY --mode hybrid --exclude-subject islam --full-text -k 8`. "
                "Public web research is also allowed.",
            )
        return (
            "Every parent and child model call must use OpenRouter. Use only the approved "
            "question and public context.",
            "Use public web sources only. Do not access local files, the local library, private "
            "repositories, internal notes, personal data, or non-public context.",
        )
