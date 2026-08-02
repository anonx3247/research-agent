from research_agent.config import load_config
from research_agent.pricing import estimate_cost


def test_estimates_include_parent_and_worker_token_budgets() -> None:
    config = load_config()
    private = estimate_cost(config, config.routes["private"], 3)
    open_cost = estimate_cost(config, config.routes["open"], 3)

    assert 0 < open_cost < private < config.settings.max_cost_usd
