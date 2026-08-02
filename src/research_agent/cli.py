from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .contracts import AppConfig, Route
from .hermes import HermesRunner
from .pricing import estimate_cost, refresh_openrouter_prices
from .workflow import ResearchWorkflow


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research-agent",
        description="Run a small, cost-capped Hermes deep research workflow.",
    )
    parser.add_argument("--config", type=Path, help="Alternative models.toml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Plan, research, verify, and synthesize")
    run.add_argument("question", nargs="?", help="Research question")
    run.add_argument("--question-file", type=Path, help="Read the question from a file")
    run.add_argument("--mode", choices=("private", "open"))
    run.add_argument("--workers", type=int)
    run.add_argument("--max-cost", type=float)
    run.add_argument("--yes", action="store_true", help="Skip cost confirmation")
    run.add_argument("--dry-run", action="store_true", help="Estimate without model calls")
    run.add_argument("--output", type=Path, default=Path("report.md"))
    run.add_argument("--usage-output", type=Path)
    run.add_argument(
        "--no-price-refresh",
        action="store_true",
        help="Use configured prices without refreshing OpenRouter prices",
    )

    estimate = subparsers.add_parser("estimate", help="Print a preflight estimate")
    estimate.add_argument("--mode", required=True, choices=("private", "open"))
    estimate.add_argument("--workers", type=int)
    estimate.add_argument("--no-price-refresh", action="store_true")
    return parser


def _select_mode(mode: str | None) -> str:
    if mode:
        return mode
    if not sys.stdin.isatty():
        raise ValueError("--mode is required in non-interactive use")
    answer = input("Run privately through Tinfoil or openly through OpenRouter? [private/open] ")
    normalized = answer.strip().lower()
    if normalized not in {"private", "open"}:
        raise ValueError("mode must be 'private' or 'open'")
    return normalized


def _question(args: argparse.Namespace) -> str:
    if args.question and args.question_file:
        raise ValueError("provide either a question argument or --question-file, not both")
    if args.question_file:
        return args.question_file.expanduser().read_text(encoding="utf-8").strip()
    if args.question:
        return args.question.strip()
    raise ValueError("a question or --question-file is required")


def _route(config: AppConfig, mode: str, refresh: bool) -> Route:
    route = config.routes[mode]
    if refresh and mode == "open":
        try:
            route = refresh_openrouter_prices(route)
        except Exception as error:
            print(f"Warning: using configured prices; refresh failed: {error}", file=sys.stderr)
    return route


def _print_estimate(route: Route, workers: int, estimate: float, ceiling: float) -> None:
    print(f"Mode:       {route.name}")
    print(f"Parent:     {route.planner.provider}/{route.planner.model}")
    print(f"Workers:    {workers} × {route.worker.provider}/{route.worker.model}")
    print(f"Synthesis:  {route.synthesis.provider}/{route.synthesis.model}")
    print(f"Estimate:   ${estimate:.2f}")
    print(f"Hard cap:   ${ceiling:.2f}")


def _run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    mode = _select_mode(args.mode)
    question = _question(args)
    workers = args.workers or config.settings.workers
    max_cost = args.max_cost or config.settings.max_cost_usd
    route = _route(config, mode, not args.no_price_refresh)
    estimated = estimate_cost(config, route, workers)
    _print_estimate(route, workers, estimated, max_cost)

    if estimated > max_cost:
        raise ValueError(f"estimated cost ${estimated:.2f} exceeds the ${max_cost:.2f} hard cap")
    if args.dry_run:
        return 0
    if not args.yes:
        if not sys.stdin.isatty():
            raise ValueError("confirmation required; pass --yes for non-interactive use")
        if input("Proceed? [y/N] ").strip().lower() not in {"y", "yes"}:
            print("Cancelled.")
            return 0

    runner = HermesRunner(
        command=config.settings.hermes_command,
        timeout_seconds=config.settings.timeout_seconds,
    )
    result = ResearchWorkflow(config, runner).run(
        question=question,
        route=route,
        worker_count=workers,
    )
    if result.usage.estimated_cost_usd >= max_cost:
        raise RuntimeError(
            f"reported cost ${result.usage.estimated_cost_usd:.2f} reached the "
            f"${max_cost:.2f} ceiling"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result.text.rstrip() + "\n", encoding="utf-8")
    usage_path = args.usage_output or args.output.with_suffix(".usage.json")
    usage_path.write_text(
        json.dumps(result.usage.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nReport: {args.output}")
    print(f"Usage:  {usage_path}")
    print(f"Actual reported cost: ${result.usage.estimated_cost_usd:.2f}")
    return 0


def _estimate(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    workers = args.workers or config.settings.workers
    route = _route(config, args.mode, not args.no_price_refresh)
    estimated = estimate_cost(config, route, workers)
    _print_estimate(route, workers, estimated, config.settings.max_cost_usd)
    return 0


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        code = _run(args) if args.command == "run" else _estimate(args)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    raise SystemExit(code)


if __name__ == "__main__":
    main()
