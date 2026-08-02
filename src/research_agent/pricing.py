from __future__ import annotations

import json
import urllib.request
from dataclasses import replace
from typing import Any

from .contracts import AppConfig, ModelSpec, Route

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


def _cost(model: ModelSpec, input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * model.input_price / 1_000_000
        + output_tokens * model.output_price / 1_000_000
    )


def estimate_cost(config: AppConfig, route: Route, workers: int) -> float:
    budgets = config.token_budgets
    worker_attempts = workers + min(config.settings.worker_retries, 1)
    return (
        _cost(route.planner, budgets["planner"].input, budgets["planner"].output)
        + worker_attempts * _cost(route.worker, budgets["worker"].input, budgets["worker"].output)
        + _cost(route.synthesis, budgets["synthesis"].input, budgets["synthesis"].output)
    )


def refresh_openrouter_prices(route: Route, timeout_seconds: float = 5.0) -> Route:
    specs = (route.planner, route.worker, route.synthesis)
    if not any(spec.provider == "openrouter" for spec in specs):
        return route

    request = urllib.request.Request(
        OPENROUTER_MODELS_URL,
        headers={"User-Agent": "local-research-agent/0.1"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload = json.load(response)
    catalog = {item["id"]: item for item in payload.get("data", [])}

    def refresh(spec: ModelSpec) -> ModelSpec:
        if spec.provider != "openrouter" or spec.model not in catalog:
            return spec
        pricing: dict[str, Any] = catalog[spec.model].get("pricing", {})
        return replace(
            spec,
            input_price=float(pricing.get("prompt", 0.0)) * 1_000_000,
            output_price=float(pricing.get("completion", 0.0)) * 1_000_000,
        )

    return replace(
        route,
        planner=refresh(route.planner),
        worker=refresh(route.worker),
        synthesis=refresh(route.synthesis),
    )
