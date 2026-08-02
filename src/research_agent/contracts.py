from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    input_price: float
    output_price: float
    toolsets: tuple[str, ...] = ()


@dataclass(frozen=True)
class Route:
    name: str
    label: str
    planner: ModelSpec
    worker: ModelSpec
    synthesis: ModelSpec


@dataclass(frozen=True)
class Settings:
    workers: int
    max_workers: int
    max_cost_usd: float
    worker_retries: int
    parent_max_iterations: int
    hermes_command: str
    timeout_seconds: int


@dataclass(frozen=True)
class TokenBudget:
    input: int
    output: int


@dataclass(frozen=True)
class AppConfig:
    settings: Settings
    routes: dict[str, Route]
    token_budgets: dict[str, TokenBudget]


@dataclass(frozen=True)
class Usage:
    estimated_cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    api_calls: int = 0
    model: str | None = None
    provider: str | None = None
    session_id: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Usage:
        return cls(
            estimated_cost_usd=float(value.get("estimated_cost_usd") or 0.0),
            input_tokens=int(value.get("input_tokens") or 0),
            output_tokens=int(value.get("output_tokens") or 0),
            reasoning_tokens=int(value.get("reasoning_tokens") or 0),
            api_calls=int(value.get("api_calls") or 0),
            model=value.get("model"),
            provider=value.get("provider"),
            session_id=value.get("session_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InvocationResult:
    text: str
    usage: Usage
