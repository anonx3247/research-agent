from __future__ import annotations

import tomllib
from importlib.resources import files
from pathlib import Path
from typing import Any

from .contracts import AppConfig, ModelSpec, Route, Settings, TokenBudget


def _model_spec(value: dict[str, Any]) -> ModelSpec:
    return ModelSpec(
        provider=str(value["provider"]),
        model=str(value["model"]),
        input_price=float(value["input_price"]),
        output_price=float(value["output_price"]),
        toolsets=tuple(str(item) for item in value.get("toolsets", [])),
    )


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or Path(str(files("research_agent").joinpath("data/models.toml")))
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    settings = Settings(**raw["settings"])
    routes = {
        name: Route(
            name=name,
            label=str(value["label"]),
            planner=_model_spec(value["planner"]),
            worker=_model_spec(value["worker"]),
            synthesis=_model_spec(value["synthesis"]),
        )
        for name, value in raw["routes"].items()
    }
    token_budgets = {
        name: TokenBudget(input=int(value["input"]), output=int(value["output"]))
        for name, value in raw["token_budget"].items()
    }
    return AppConfig(settings=settings, routes=routes, token_budgets=token_budgets)
